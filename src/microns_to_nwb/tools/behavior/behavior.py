import numpy as np
from hdmf.backends.hdf5 import H5DataIO
from phase3 import nda
from pynwb import TimeSeries
from pynwb.behavior import PupilTracking, SpatialSeries, EyeTracking


def add_eye_tracking(scan_key, nwb):
    pupil_min_r, pupil_maj_r, pupil_x, pupil_y, timestamps = (nda.RawManualPupil() & scan_key).fetch1(
        "pupil_min_r", "pupil_maj_r", "pupil_x", "pupil_y", "pupil_times"
    )

    pupil_min_r = TimeSeries(
        name="pupil_min_r",
        description="minor axis of pupil tracking ellipse",
        data=H5DataIO(pupil_min_r, compression=True),
        timestamps=H5DataIO(timestamps, compression=True),
        unit="n.a.",
    )

    pupil_maj_r = TimeSeries(
        name="pupil_maj_r",
        description="jajor axis of pupil tracking ellipse",
        data=H5DataIO(pupil_maj_r, compression=True),
        timestamps=pupil_min_r,
        unit="n.a.",
    )

    pupil_tracking = PupilTracking([pupil_min_r, pupil_maj_r])
    nwb.add_acquisition(pupil_tracking)

    pupil_xy = SpatialSeries(
        name="eye_position",
        description="x,y position of eye",
        data=H5DataIO(np.c_[pupil_x, pupil_y], compression=True),
        timestamps=pupil_min_r,
        unit="n.a.",
        reference_frame="unknown",
    )

    eye_position_tracking = EyeTracking(pupil_xy)

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
