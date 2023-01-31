from pathlib import Path

import numpy as np
import pandas as pd
from neuroconv.utils import FilePathType
from phase3 import nda
from itertools import repeat

from scipy.interpolate import interp1d
from tqdm import tqdm


def reconstruct_refresh_rate_flips(trial_key, intertrial_time, tol, est_refresh_rate):
    """
    Author: Paul Fahey
    Fetch trial flips, reformats to monitor refresh rate including intertrial times

    Args:
        trial_key                      restricts to single trial in single scan
        intertrial_time                time from last flip of trial to first flip of following trial (sec)
        tol:float                      tolerance for flip time deviation from expected frame rate (sec)
        est_refresh_rate:int           estimated underlying monitor refresh rate, Hz

    Returns:
        trial_flip_times:np.array      resampled monitor flip times for the trial, inc following intertrial period
    """

    # get trial rel with flip times and frame rate information for appropriate stimulus type
    cond_rel = nda.Trial & trial_key
    stim_type = cond_rel.fetch1("type")
    stim_table_lookup = {"stimulus.Clip": nda.Clip, "stimulus.Monet2": nda.Monet2, "stimulus.Trippy": nda.Trippy}
    cond_rel = cond_rel * stim_table_lookup[stim_type]

    # fetch trial flip times and frame rate
    if stim_type == "stimulus.Clip":
        frame_rate = 30.0
        flip_times = cond_rel.fetch1("frame_times")
    else:
        flip_times, frame_rate = cond_rel.fetch1("frame_times", "fps")
        frame_rate = float(frame_rate)

    # estimate upsample ratio as integer multiple of frame rate
    assert ((est_refresh_rate / frame_rate) % 1) == 0, "refresh rate not integer multiple of frame rate"
    upsample_ratio = int(est_refresh_rate / frame_rate)

    # detect deviant flips with abnormal frame rates
    # note: only session 8 scan 9 had intratrial hanging frames, trial 0, total 33 ms intratrial delay
    dev_flips = np.abs(np.diff(flip_times) - (1 / frame_rate)) > tol

    if np.any(dev_flips):
        # split into blocks of uniform frame rates with hanging final frame
        dev_flip_frames = np.diff(flip_times)[0][np.where(dev_flips)[1]] * est_refresh_rate
        assert np.all(
            (np.abs(np.round(dev_flip_frames) - dev_flip_frames) / est_refresh_rate) < tol
        ), "non-integer dropped frames detected"
        print(f"intratrial dropped frames detected, filling independently at {est_refresh_rate} Hz")
        print(trial_key)

        interblock_times = [*np.diff(flip_times)[0][np.where(dev_flips)[1]], intertrial_time]
        block_flip_sets = [np.asarray(a) for a in np.split(flip_times[0], np.where(dev_flips)[1] + 1)]
    else:
        # if not deviant frames format as list for iteration of 1
        interblock_times = [intertrial_time]
        block_flip_sets = [flip_times]

    trial_flip_times, trial_movie = [], []
    for interblock_time, block_flips in zip(interblock_times, block_flip_sets):

        assert np.all(np.abs(np.diff(block_flips) - (1 / frame_rate)) < tol), "frame rate deviation > 1 ms detected"

        # last flip and interblock period at refresh rate
        interblock_frames = (np.round(interblock_time * est_refresh_rate) - 1).astype(int)

        # linearly interpolated interblock flip times at refresh rate
        interblock_flip_times = np.linspace(block_flips[-1], block_flips[-1] + interblock_time, interblock_frames + 2)[
            0:-1
        ]

        if upsample_ratio > 1:
            # index to flip time linear interpolation
            idx2ft = interp1d(
                np.arange(0, len(block_flips) * upsample_ratio, upsample_ratio), block_flips, kind="linear"
            )

            # linearly interpolated intrablock flip times at refresh rate
            intrablock_flip_times = idx2ft(np.arange(0, (len(block_flips) - 1) * upsample_ratio))

        elif upsample_ratio == 1:
            intrablock_flip_times = block_flips[:-1]

        # concatenate interblock/intertrial to block
        trial_flip_times.append(np.concatenate((intrablock_flip_times, interblock_flip_times)))

    # concatenate blocks to trial
    trial_flip_times = np.concatenate(trial_flip_times, axis=0)

    return trial_flip_times


def resample_flips(scan_key, tol=2e-3, est_refresh_rate=60):
    """
    Author: Paul Fahey
    Fetch stimulus flips, reformats to monitor refresh rate including intertrial times and pre/post stimulus

    Args:
        scan_key                       restricts to all trials of a single scan
        tol:float                      tolerance for flip time deviation from expected frame rate (sec)
        est_refresh_rate:int           estimated underlying monitor refresh rate (Hz)

    Returns:

        full_flips:np.array            combined recorded and inferred flip times of full stimulus
        emp_refresh_rate:float         empirical mean refresh rate of monitor
    """
    assert len(nda.Scan & scan_key) == 1, "scan_key does not restrict to a single scan"

    # get all trial keys and corresponding stimulus types
    trial_rel = nda.Trial & scan_key
    trial_keys, flip_times = trial_rel.fetch("KEY", "frame_times", order_by="trial_idx ASC")
    intertrial_times = np.array([flip_times[i + 1][0] - flip_times[i][-1] for i in range(len(flip_times) - 1)])

    # empirical frame rate in stimulus clock
    emp_refresh_rate = 1 / np.mean(
        np.hstack([np.diff(ft) for ft in flip_times if (1 / np.mean(np.diff(ft))) > (0.75 * est_refresh_rate)])
    )

    # assume median intertrial_period approximates final intertrial period following last trial
    intertrial_times = np.append(intertrial_times, np.median(intertrial_times))

    # check that intertrial time is integer multiple of refresh frame rate
    assert np.all(
        np.abs(np.round(intertrial_times * est_refresh_rate) - (intertrial_times * est_refresh_rate)) < tol
    ), f"intertrial frame rate deviation > {np.round(tol * 1000).astype(int)} ms detected"

    # for each trial, get the flip times at monitor refresh rate, including following intertrial
    trial_iter = zip(trial_keys, intertrial_times, repeat(tol), repeat(est_refresh_rate))
    all_trial_flips = np.concatenate(
        [
            reconstruct_refresh_rate_flips(*t)
            for t in tqdm(trial_iter, total=len(trial_keys), desc="Reconstructing stimulus movie timestamps ...")
        ]
    )

    # get scan start/end info
    scan_times, ndepths = (nda.FrameTimes & scan_key).fetch1("frame_times", "ndepths")

    # get time of first field in first frame of scan
    scan_onset_time = scan_times[0]

    # get time of last field in last frame of scan
    # last ScanTime is for start of first depth, must add other depths
    # to estimate scan offset when all depths complete
    if scan_key == {"session": 4, "scan_idx": 9}:
        # this scan was interrupted without completing a full set of depths for the last frame
        extra_frames = (ndepths - 1) + 3
    else:
        extra_frames = ndepths - 1
    interdepth_time = np.mean(np.diff(scan_times)) / ndepths
    scan_offset_time = scan_times[-1] + (extra_frames * interdepth_time)

    # detect scan duration preceding stimulus onset, create prepad flips at refresh rate to encompass
    prepad_frames = np.ceil((all_trial_flips[0] - scan_onset_time) * emp_refresh_rate).astype(int)
    prepad_flips = np.linspace(
        all_trial_flips[0] - (prepad_frames / emp_refresh_rate), all_trial_flips[0], prepad_frames, endpoint=False
    )

    # detect scan duration following stimulus offset, create postpad flips at refresh rate to encompass
    postpad_frames = np.ceil((scan_offset_time - all_trial_flips[-1]) * emp_refresh_rate).astype(int)
    postpad_flips = np.linspace(
        all_trial_flips[-1], all_trial_flips[-1] + postpad_frames / emp_refresh_rate, postpad_frames + 1, endpoint=True
    )[1:]

    full_flips = np.concatenate((prepad_flips, all_trial_flips, postpad_flips))

    return full_flips, emp_refresh_rate


def get_stimulus_movie_timestamps(scan_key, file_path: FilePathType = None):
    if file_path is not None and Path(file_path).is_file():
        return pd.read_csv(file_path)["timestamps"].values

    stimulus_timestamps, _ = resample_flips(scan_key=scan_key)
    # Write to CSV for faster read when conversion is needed to rerun
    pd.DataFrame(data=stimulus_timestamps, columns=["timestamps"]).to_csv(file_path, index=False)

    return stimulus_timestamps
