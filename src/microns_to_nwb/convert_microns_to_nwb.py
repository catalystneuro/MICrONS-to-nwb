from warnings import warn

from phase3 import nda

from tools.behavior import add_eye_tracking, add_treadmill, find_earliest_timestamp
from tools.intervals import add_trials
from tools.nwb_helpers import start_nwb
from tools.ophys import add_ophys
from tools.stimulus import add_stimulus


def build_nwb(scan_key):
    nwb = start_nwb(scan_key)
    add_stimulus(scan_key, nwb)

    # Shifting times to earliest provided behavioral timestamp when necessary
    pupil_timestamps = (nda.RawManualPupil & scan_key).fetch1("pupil_times")
    treadmill_timestamps = (nda.RawTreadmill & scan_key).fetch1("treadmill_timestamps")
    frame_times = (nda.FrameTimes & scan_key).fetch1("frame_times")
    trial_start_times, trial_stop_times = (nda.Trial & scan_key).fetch("start_frame_time", "end_frame_time", order_by="trial_idx")

    first_timestamp_in_behavior = find_earliest_timestamp([pupil_timestamps, treadmill_timestamps])
    if first_timestamp_in_behavior < 0:
        warn(
            "Writing behavior data to NWB with negative timestamps is not recommended,"
            f"times are shifted to the earliest behavioral timestamp by {abs(first_timestamp_in_behavior)} seconds."
        )
        pupil_timestamps = pupil_timestamps + abs(first_timestamp_in_behavior)
        treadmill_timestamps = treadmill_timestamps + abs(first_timestamp_in_behavior)
        frame_times = frame_times + abs(first_timestamp_in_behavior)
        trial_start_times = trial_start_times + abs(first_timestamp_in_behavior)
        trial_stop_times = trial_stop_times + abs(first_timestamp_in_behavior)

    add_eye_tracking(scan_key, nwb, timestamps=pupil_timestamps)
    add_treadmill(scan_key, nwb, timestamps=treadmill_timestamps)
    add_trials(scan_key, nwb, timestamps=(trial_start_times, trial_stop_times))
    add_ophys(scan_key, nwb, timestamps=frame_times)

    return nwb
