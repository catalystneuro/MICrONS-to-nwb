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
    image_height, image_width = (nda.Field & field_key).fetch1("px_height", "px_width")
    mask_pixels, mask_weights, mask_ids, mask_types = (nda.Segmentation * nda.MaskClassification & field_key).fetch(
        "pixels", "weights", "mask_id", "mask_type", order_by="mask_id"
    )

    plane_segmentation = image_segmentation.create_plane_segmentation(
        name=f"PlaneSegmentation{field_key['field']}",
        description="output from segmenting my favorite imaging plane",
        imaging_plane=imaging_plane,
        id=mask_ids,
    )

    # Reshape masks
    masks = func.reshape_masks(mask_pixels, mask_weights, image_height, image_width)
    # The masks dimensions are (width, height, number of frames), for NWB it should be
    # transposed to (number of frames, width, height)
    masks = masks.transpose(2, 0, 1)

    # Add image masks
    plane_segmentation.add_column(
        name="image_mask",
        description="The image masks for each ROI.",
        data=H5DataIO(masks, compression=True),
    )

    # Add type of ROIs
    plane_segmentation.add_column(
        name="mask_type",
        description="The classification of mask as soma or artifact.",
        data=mask_types.astype(str),
    )

    return plane_segmentation


def _get_fluorescence(nwb, fluorescence_name):
    ophys = check_module(nwb, "ophys")

    if fluorescence_name in ophys.data_interfaces:
        return ophys.get(fluorescence_name)

    fluorescence = Fluorescence(name=fluorescence_name)
    ophys.add(fluorescence)

    return fluorescence


def add_roi_response_series(scan_key, field_key, nwb, plane_segmentation):
    frame_times = (nda.FrameTimes & scan_key).fetch1("frame_times")

    traces_for_each_mask = (nda.Fluorescence() & field_key).fetch("trace", order_by="mask_id")
    continuous_traces = np.vstack(traces_for_each_mask).T

    roi_table_region = plane_segmentation.create_roi_table_region(
        region=list(range(continuous_traces.shape[1])), description=f"all rois in field {field_key['field']}"
    )

    roi_response_series = RoiResponseSeries(
        name=f"RioResponseSeries{field_key['field']}",
        description=f"The fluorescence traces for field {field_key['field']}",
        data=H5DataIO(continuous_traces, compression=True),
        rois=roi_table_region,
        timestamps=H5DataIO(frame_times, compression=True),
        units="n.a.",
    )

    fluorescence = _get_fluorescence(nwb=nwb, fluorescence_name="Fluorescence")
    fluorescence.add_roi_response_series(roi_response_series)


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
        field_x_in_meters = field_data["field_x"] / 1e6
        field_y_in_meters = field_data["field_y"] / 1e6
        field_z_in_meters = field_data["field_z"] / 1e6
        field_width_in_meters = field_data["um_width"] / 1e6
        field_height_in_meters = field_data["um_height"] / 1e6
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
                field_width_in_meters / field_data["px_width"],
                field_height_in_meters / field_data["px_height"],
            ],
            grid_spacing_unit="meters",
            origin_coords=[field_x_in_meters, field_y_in_meters, field_z_in_meters],
            origin_coords_unit="meters",
        )

        field_key = {**scan_key, **dict(field=field_data["field"])}

        plane_segmentation = add_plane_segmentation(field_key, nwb, imaging_plane, image_segmentation)
        add_roi_response_series(scan_key, field_key, nwb, plane_segmentation)
        add_summary_images(field_key, nwb)
