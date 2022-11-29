from phase3 import nda


def add_trials(scan_key, nwb):
    nwb.add_trial_column("condition_hash", "condition hash")
    nwb.add_trial_column("stimulus_type", "stimulus type")

    stimulus_types, start_times, stop_times, condition_hashes, trial_idxs = (nda.Trial & scan_key).fetch(
        "type", "start_frame_time", "end_frame_time", "condition_hash", "trial_idx", order_by="trial_idx"
    )

    for stimulus_type, start_time, stop_time, condition_hash, trial_idx in zip(
        stimulus_types, start_times, stop_times, condition_hashes, trial_idxs
    ):
        nwb.add_trial(
            id=trial_idx,
            start_time=start_time,
            stop_time=stop_time,
            stimulus_type=stimulus_type,
            condition_hash=condition_hash,
        )
