from typing import Tuple, Optional

import numpy as np

from neuroconv.utils import FilePathType, FloatType
from roiextractors import ImagingExtractor
from tifffile import memmap, TiffFile


class MicronsTiffImagingExtractor(ImagingExtractor):
    extractor_name = "MicronsTiffImaging"
    is_writable = True
    mode = "file"

    def __init__(
        self,
        file_path: FilePathType,  # file path to TIF file
        sampling_frequency: FloatType,
        plane_index: int,  # the field index
        num_frames_per_plane: int,
    ):
        self.file_path = file_path
        super().__init__()

        self._sampling_frequency = sampling_frequency
        self._plane_index = plane_index
        self._num_frames = num_frames_per_plane

        with TiffFile(self.file_path) as tif:
            shape = tif.series[0].shape
            self._dtype = tif.series[0].dtype

        self._video = memmap(self.file_path, mode="r")

        assert shape[0] % self._num_frames == 0
        self._num_planes = int(shape[0] / self._num_frames)
        self._frames_range = np.arange(self._plane_index, self._num_planes * self._num_frames, self._num_planes)

        self._num_channels = 1
        self._num_rows, self._num_columns = shape[1:]

    def get_frames(self, frame_idxs, channel: int = 0):
        return self._video[self._frames_range[frame_idxs], :, :]

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

        return self._video[self._frames_range[start_frame:end_frame], :, :]

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
        return self._dtype
