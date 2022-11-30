import numpy as np
from hdmf.backends.hdf5 import H5DataIO
from phase3 import nda
from pynwb import TimeSeries
from pynwb.behavior import PupilTracking, SpatialSeries, EyeTracking


def add_eye_tracking(scan_key, nwb):
    pupil_minor_radius_data, pupil_major_radius_data, pupil_x, pupil_y, timestamps = (
        nda.RawManualPupil() & scan_key
    ).fetch1("pupil_min_r", "pupil_maj_r", "pupil_x", "pupil_y", "pupil_times")

    pupil_minor_radius = TimeSeries(
        name="pupil_minor_radius",
        description="Minor radius extracted from the pupil tracking ellipse.",
        data=H5DataIO(pupil_minor_radius_data, compression=True),
        timestamps=H5DataIO(timestamps, compression=True),
        unit="n.a.",
    )

    pupil_major_radius = TimeSeries(
        name="pupil_major_radius",
        description="Major radius extracted from the pupil tracking ellipse.",
        data=H5DataIO(pupil_major_radius_data, compression=True),
        timestamps=pupil_minor_radius,
        unit="n.a.",
    )

    pupil_tracking = PupilTracking(time_series=[pupil_minor_radius, pupil_major_radius])
    nwb.add_acquisition(pupil_tracking)

    eye_position = SpatialSeries(
        name="eye_position",
        description="The x,y position of the pupil.",
        data=H5DataIO(np.c_[pupil_x, pupil_y], compression=True),
        timestamps=pupil_minor_radius,
        unit="n.a.",
        reference_frame="unknown",
    )

    eye_position_tracking = EyeTracking(eye_position)

    nwb.add_acquisition(eye_position_tracking)


def add_treadmill(scan_key, nwb):
    treadmill_velocity, treadmill_timestamps = (nda.RawTreadmill & scan_key).fetch1(
        "treadmill_velocity", "treadmill_timestamps"
    )

    treadmill_velocity = TimeSeries(
        name="treadmill_velocity",
        data=H5DataIO(treadmill_velocity, compression=True),
        timestamps=H5DataIO(treadmill_timestamps, compression=True),
        description="velocity of treadmill",
        unit="m/s",
        conversion=0.01,
    )

    nwb.add_acquisition(treadmill_velocity)
