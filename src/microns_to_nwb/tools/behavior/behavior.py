import numpy as np
from hdmf.backends.hdf5 import H5DataIO
from phase3 import nda
from pynwb import TimeSeries
from pynwb.behavior import PupilTracking, SpatialSeries, EyeTracking


def add_eye_tracking(scan_key, nwb, timestamps):
    pupil_minor_radius_data, pupil_major_radius_data, pupil_x, pupil_y = (
        nda.RawManualPupil & scan_key
    ).fetch1("pupil_min_r", "pupil_maj_r", "pupil_x", "pupil_y")

    good_indices = _crop_indices(pupil_minor_radius_data)

    pupil_minor_radius = TimeSeries(
        name="pupil_minor_radius",
        description="Minor radius extracted from the pupil tracking ellipse."
        "The values are estimated in the relative pixel units.",
        data=H5DataIO(pupil_minor_radius_data[good_indices], compression=True),
        timestamps=H5DataIO(timestamps[good_indices], compression=True),
        unit="px",
    )

    pupil_major_radius = TimeSeries(
        name="pupil_major_radius",
        description="Major radius extracted from the pupil tracking ellipse."
        "The values are estimated in the relative pixel units.",
        data=H5DataIO(pupil_major_radius_data[good_indices], compression=True),
        timestamps=pupil_minor_radius,
        unit="px",
    )

    pupil_tracking = PupilTracking(time_series=[pupil_minor_radius, pupil_major_radius])
    nwb.add_acquisition(pupil_tracking)

    pupil_x_position = np.array(pupil_x)[good_indices]
    pupil_y_position = np.array(pupil_y)[good_indices]

    eye_position = SpatialSeries(
        name="eye_position",
        description="The x,y position of the pupil." "The values are estimated in the relative pixel units.",
        data=H5DataIO(np.c_[pupil_x_position, pupil_y_position], compression=True),
        timestamps=pupil_minor_radius,
        unit="px",
        reference_frame="unknown",
    )

    eye_position_tracking = EyeTracking(eye_position)

    nwb.add_acquisition(eye_position_tracking)


def add_treadmill(scan_key, nwb, timestamps):
    treadmill_velocity = (nda.RawTreadmill & scan_key).fetch1("treadmill_velocity",)

    good_indices = _crop_indices(behavior_data=treadmill_velocity)

    treadmill_velocity_raw = TimeSeries(
        name="treadmill_velocity",
        data=H5DataIO(treadmill_velocity[good_indices], compression=True),
        timestamps=H5DataIO(timestamps[good_indices], compression=True),
        description="Cylindrical treadmill rostral-caudal position extracted at ~60-100 Hz and converted into velocity.",
        unit="m/s",
        conversion=0.01,
    )

    nwb.add_acquisition(treadmill_velocity_raw)


def _crop_indices(behavior_data):
    data_array = np.array(behavior_data)
    last_value_index = data_array.shape[0]

    # find the index of first non-missing value
    first_value_index = np.isnan(data_array).argmin()

    if np.isnan(data_array[-1]):
        # find the index of the last non-missing value
        last_value_index = data_array.shape[0] - np.isnan(data_array[::-1]).argmin()

    indices = np.arange(first_value_index, last_value_index)
    return indices


def find_earliest_timestamp(behavior_timestamps_arrays):
    return min(
        [timestamps[np.isnan(timestamps).argmin()] for timestamps in behavior_timestamps_arrays],
    )
