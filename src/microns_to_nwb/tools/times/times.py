import pandas as pd


def get_frame_times(scan_key: dict, file_path: str):
    frame_times = pd.read_pickle(file_path)

    frame_times_for_this_scan = frame_times[
        (frame_times["session"] == int(scan_key["session"])) & (frame_times["scan_idx"] == int(scan_key["scan_idx"]))
    ]["frame_times"].values[0]

    return frame_times_for_this_scan


def get_trial_times(scan_key: dict, file_path: str):
    trial_times = pd.read_pickle(file_path)

    trial_times_for_this_scan = trial_times[
        (trial_times["session"] == int(scan_key["session"])) & (trial_times["scan_idx"] == int(scan_key["scan_idx"]))
    ]

    return trial_times_for_this_scan


def get_stimulus_times(scan_key: dict, file_path: str):
    stimulus_times = pd.read_pickle(file_path)

    stimulus_times_for_this_scan = stimulus_times[
        (stimulus_times["session"] == int(scan_key["session"]))
        & (stimulus_times["scan_idx"] == int(scan_key["scan_idx"]))
    ]["full_flips"].values[0]

    return stimulus_times_for_this_scan
