import numpy as np
from hdmf.backends.hdf5 import H5DataIO
from phase3 import nda, func
from pynwb.base import Images
from pynwb.image import GrayscaleImage
from pynwb.ophys import (
    RoiResponseSeries,
    Fluorescence,
    ImageSegmentation,
    OpticalChannel,
)

from tools.nwb_helpers import check_module


def add_summary_images(field_key, nwb):
    ophys = check_module(nwb, "ophys")

    correlation_image_data, average_image_data = (nda.SummaryImages & field_key).fetch1("correlation", "average")

    # The image dimensions are (height, width), for NWB it should be transposed to (width, height).
    correlation_image_data = correlation_image_data.transpose(1, 0)
    correlation_image = GrayscaleImage(
        name="correlation",
        data=correlation_image_data,
    )
    average_image_data = average_image_data.transpose(1, 0)
    average_image = GrayscaleImage(
        name="average",
        data=average_image_data,
    )

    # Add images to Images container
    segmentation_images = Images(
        name=f"SegmentationImages{field_key['field']}",
        images=[correlation_image, average_image],
        description=f"Correlation and average images for field {field_key['field']}.",
    )
    ophys.add(segmentation_images)


def add_plane_segmentation(field_key, nwb, imaging_plane, image_segmentation):
    plane_segmentation = image_segmentation.create_plane_segmentation(
        name=f"PlaneSegmentation{field_key['field']}",
        description="output from segmenting my favorite imaging plane",
        imaging_plane=imaging_plane,
    )
    plane_segmentation.add_column("mask_type", "type of ROI")

    image_height, image_width = (nda.Field & field_key).fetch1("px_height", "px_width")

    mask_pixels, mask_weights, mask_ids, mask_types = (nda.Segmentation * nda.MaskClassification & field_key).fetch(
        "pixels", "weights", "mask_id", "mask_type", order_by="mask_id"
    )

    # Reshape masks
    masks = func.reshape_masks(mask_pixels, mask_weights, image_height, image_width)

    for image_mask, mask_id, mask_type in zip(masks, mask_ids, mask_types):
        plane_segmentation.add_roi(
            image_mask=image_mask,
            id=mask_id,
            mask_type=mask_type,
        )

    return plane_segmentation


def add_roi_response_series(scan_key, field_key, nwb, plane_segmentation):
    frame_times = (nda.FrameTimes & scan_key).fetch1("frame_times")

    data = np.vstack((nda.Fluorescence() & field_key).fetch("trace", order_by="mask_id")).T

    rt_region = plane_segmentation.create_roi_table_region(
        region=list(range(data.shape[1])), description=f"all rois in field {field_key['field']}"
    )

    roi_response_series = RoiResponseSeries(
        name=f"RioResponseSeries{field_key['field']}",
        description=f"traces for field {field_key['field']}",
        data=H5DataIO(data, compression=True),
        rois=rt_region,
        timestamps=H5DataIO(frame_times, compression=True),
        units="n/a",
    )

    fluorescence = Fluorescence()
    fluorescence.add(roi_response_series)


def add_ophys(scan_key, nwb):
    device = nwb.create_device(
        name="Microscope",
        description="two-photon random access mesoscope",
    )
    ophys = nwb.create_processing_module("ophys", "processed 2p data")
    image_segmentation = ImageSegmentation()
    ophys.add(image_segmentation)
    all_field_data = (nda.Field & scan_key).fetch(as_dict=True)
    for field_data in all_field_data:
        optical_channel = OpticalChannel(
            name="OpticalChannel",
            description="an optical channel",
            emission_lambda=500.0,
        )
        imaging_plane = nwb.create_imaging_plane(
            name=f"ImagingPlane{field_data['field']}",
            optical_channel=optical_channel,
            imaging_rate=np.nan,
            description="no description",
            device=device,
            excitation_lambda=920.0,
            indicator="GCaMP6",
            location="unknown",
            grid_spacing=[
                field_data["um_width"] / field_data["px_width"] * 1e-6,
                field_data["um_height"] / field_data["px_height"],
            ],
            grid_spacing_unit="meters",
            origin_coords=[field_data["field_x"], field_data["field_y"], field_data["field_z"]],
            origin_coords_unit="meters",
        )

        field_key = {**scan_key, **dict(field=field_data["field"])}

        plane_segmentation = add_plane_segmentation(field_key, nwb, imaging_plane, image_segmentation)
        add_roi_response_series(scan_key, field_key, nwb, plane_segmentation)
        add_summary_images(field_key, nwb)
