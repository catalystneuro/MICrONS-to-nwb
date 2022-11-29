from tools.behavior import add_eye_tracking, add_treadmill
from tools.intervals import add_trials
from tools.nwb_helpers import start_nwb
from tools.ophys import add_ophys


def build_nwb(scan_key):
    nwb = start_nwb(scan_key)
    # add_stimulus(scan_key, nwb)
    add_eye_tracking(scan_key, nwb)
    add_treadmill(scan_key, nwb)
    add_trials(scan_key, nwb)
    add_ophys(scan_key, nwb)

    return nwb
