from typing import Tuple, Optional

import numpy as np
import zarr
from fsspec import filesystem
from fsspec.implementations.cached import CachingFileSystem
from neuroconv.utils import FilePathType, FloatType
from roiextractors import ImagingExtractor
from tifffile import imread


class MicronsTiffImagingExtractor(ImagingExtractor):
    extractor_name = "MicronsTiffImaging"
    is_writable = True
    mode = "file"

    def __init__(
        self,
        file_path: FilePathType,  # S3 file path to TIF file
        cache_storage: FilePathType,  # local cache storage for fsspec
        sampling_frequency: FloatType,
        plane_index: int,  # the field index
        num_frames_per_plane: int,
    ):
        self._s3_file = None
        self.file_path = file_path
        super().__init__()

        self._sampling_frequency = sampling_frequency
        self._plane_index = plane_index
        self._num_frames = num_frames_per_plane

        # Lazy loading of image data from S3
        self._video = self.open(cache_storage=cache_storage)

        assert self._video.shape[0] % self._num_frames == 0
        self._num_planes = int(self._video.shape[0] / self._num_frames)
        self._frames_range = np.arange(self._plane_index, self._num_planes * self._num_frames, self._num_planes)

        self._num_channels = 1
        self._num_rows, self._num_columns = self._video.shape[1:]

    def open(self, cache_storage):
        cfs = CachingFileSystem(
            fs=filesystem("s3", anon=True),
            cache_storage=cache_storage,  # Local folder for the cache
        )

        self._s3_file = cfs.open(self.file_path, "rb")
        zarr_store = imread(self._s3_file, aszarr=True)

        return zarr.open(zarr_store, mode="r")

    def close(self):
        self._s3_file.close()

    def get_frames(self, frame_idxs, channel: int = 0):
        return self._video.oindex[self._frames_range[frame_idxs], :, :]

    def get_video(self, start_frame=None, end_frame=None, channel: Optional[int] = 0):
        if start_frame is None:
            start_frame = 0
        else:
            assert 0 <= start_frame < self._num_frames
        if end_frame is None:
            end_frame = self._num_frames
        else:
            assert 0 < end_frame <= self._num_frames
        assert end_frame > start_frame, "'start_frame' must be smaller than 'end_frame'!"

        return self._video.oindex[self._frames_range[start_frame:end_frame], :, :]

    def get_image_size(self) -> Tuple[int, int]:
        return (self._num_rows, self._num_columns)

    def get_num_frames(self):
        return self._num_frames

    def get_sampling_frequency(self):
        return self._sampling_frequency

    def get_num_channels(self):
        return self._num_channels

    def get_channel_names(self):
        pass

    def get_dtype(self):
        return self._video.dtype
