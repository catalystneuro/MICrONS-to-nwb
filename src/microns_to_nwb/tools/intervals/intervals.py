from phase3 import nda
from pynwb.epoch import TimeIntervals


def add_trials(scan_key, nwb, timestamps):
    nwb.add_trial_column("condition_hash", "condition hash")
    nwb.add_trial_column("stimulus_type", "stimulus type")

    stimulus_types, condition_hashes, trial_idxs = (nda.Trial & scan_key).fetch(
        "type", "condition_hash", "trial_idx", order_by="trial_idx"
    )

    trippy_condition_hashes = []
    trippy_timestamps = []

    clip_condition_hashes = []
    clip_timestamps = []

    monet2_condition_hashes = []
    monet2_timestamps = []

    for stimulus_type, start_time, stop_time, condition_hash, trial_idx in zip(
        stimulus_types, timestamps[0], timestamps[1], condition_hashes, trial_idxs
    ):
        if "Trippy" in stimulus_type:
            trippy_condition_hashes.append(condition_hash)
            trippy_timestamps.append((start_time, stop_time))

        elif "Clip" in stimulus_type:
            clip_condition_hashes.append(condition_hash)
            clip_timestamps.append((start_time, stop_time))

        elif "Monet2" in stimulus_type:
            monet2_condition_hashes.append(condition_hash)
            monet2_timestamps.append((start_time, stop_time))

        nwb.add_trial(
            id=trial_idx,
            start_time=start_time,
            stop_time=stop_time,
            stimulus_type=stimulus_type,
            condition_hash=condition_hash,
        )

    add_trials_from_trippy(nwb, condition_hashes=trippy_condition_hashes, timestamps=trippy_timestamps)
    add_trials_from_clip(nwb, condition_hashes=clip_condition_hashes, timestamps=clip_timestamps)
    add_trials_from_monet2(nwb, condition_hashes=monet2_condition_hashes, timestamps=monet2_timestamps)


def add_trials_from_trippy(nwb, condition_hashes, timestamps):
    if not condition_hashes:
        return

    trippy_table = TimeIntervals(
        name="Trippy",
        description="The stimulus table for the cosine of a smoothened noise phase movie.",
    )

    trippy_columns = [
        ("condition_hash", "The hash for the stimulus condition."),
        ("rng_seed", "Random number generate seed for the stimulus movie."),
        ("texture_height", "Texture height in pixels."),
        ("texture_width", "Texture width in pixels."),
        ("duration", "Trial duration in seconds."),
        ("xnodes", "The x dimension of low-res phase movie."),
        ("ynodes", "The y dimension of low-res phase movie."),
        ("up_factor", "The spatial upscale factor."),
        ("temp_freq", "The temporal frequency if the phase pattern were static (Hz)."),
        (
            "temp_kernel_length",
            "The length of Hanning kernel for the temporal filter, controls the rate of change of the phase pattern.",
        ),
        ("spatial_freq", "The approximate max spatial frequency. The actual frequencies may be higher. (cy/point)."),
    ]
    for column_name, column_description in trippy_columns:
        trippy_table.add_column(column_name, column_description)

    for condition_hash, times in zip(condition_hashes, timestamps):
        hash_key = {"condition_hash": condition_hash}

        (
            rng_seed,
            texture_height,
            texture_width,
            duration,
            xnodes,
            ynodes,
            up_factor,
            temp_freq,
            temp_kernel_length,
            spatial_freq,
        ) = (nda.Trippy() & hash_key).fetch1(
            "rng_seed",
            "tex_ydim",
            "tex_xdim",
            "duration",
            "xnodes",
            "ynodes",
            "up_factor",
            "temp_freq",
            "temp_kernel_length",
            "spatial_freq",
        )

        trippy_table.add_interval(
            condition_hash=condition_hash,
            start_time=times[0],
            stop_time=times[1],
            rng_seed=rng_seed,
            texture_height=texture_height,
            texture_width=texture_width,
            duration=duration,
            xnodes=xnodes,
            ynodes=ynodes,
            up_factor=up_factor,
            temp_freq=temp_freq,
            temp_kernel_length=temp_kernel_length,
            spatial_freq=spatial_freq,
        )

    nwb.add_time_intervals(trippy_table)


def add_trials_from_clip(nwb, condition_hashes, timestamps):
    if not condition_hashes:
        return

    clip_table = TimeIntervals(
        name="Clip",
        description="Composed of 10 second clips from cinematic releases, Sports-1M dataset, or custom rendered first person POV videos in 3D environment in Unreal Engine.",
    )

    clip_columns = [
        ("condition_hash", "The hash for the stimulus condition."),
        ("movie_name", "The full clip source."),
        ("short_movie_name", "The type of the clip (cinematic, sports1m, rendered)."),
        ("duration", "The clip duration in seconds."),
    ]

    for column_name, column_description in clip_columns:
        clip_table.add_column(column_name, column_description)

    for condition_hash, times in zip(condition_hashes, timestamps):
        hash_key = {"condition_hash": condition_hash}

        movie_name, short_movie_name, duration = (nda.Clip() & hash_key).fetch1(
            "movie_name", "short_movie_name", "duration"
        )

        clip_table.add_interval(
            condition_hash=condition_hash,
            start_time=times[0],
            stop_time=times[1],
            movie_name=movie_name,
            short_movie_name=short_movie_name,
            duration=duration,
        )

    nwb.add_time_intervals(clip_table)


def add_trials_from_monet2(nwb, condition_hashes, timestamps):
    if not condition_hashes:
        return

    monet2_table = TimeIntervals(
        name="Monet2",
        description="Generated from smoothened Gaussian noise and a global orientation and direction component.",
    )

    monet2_columns = [
        ("condition_hash", "The hash for the stimulus condition."),
        ("rng_seed", "Random number generate seed for the stimulus movie."),
        ("duration", "Duration of clip in seconds."),
        ("blue_green_saturation", "0 = grayscale, 1=blue/green"),
        ("pattern_width", "The width of generated pattern (pixels)."),
        ("pattern_aspect", "The aspect ratio of generated pattern."),
        ("temp_kernel", "The temporal kernel type (hamming, half-hamming)."),
        ("temp_bandwidth", "The temporal bandwidth of the stimulus (Hz)."),
        ("ori_coherence", "1=unoriented noise. pi / ori coherence = bandwidth of orientation kernel."),
        ("ori_fraction", "The fraction of stimulus with coherent orientation vs unoriented."),
        ("ori_mix", "The mixin-coefficient of orientation biased noise."),
        ("num_directions", "The number of directions."),
        # ("speed", "units/s motion component, where unit is display width"),
        # ("directions", "computed directions of motion (deg)"),
        # ("onsets", "computed directions of motion (deg)"),
    ]

    for column_name, column_description in monet2_columns:
        monet2_table.add_column(column_name, column_description)

    for condition_hash, times in zip(condition_hashes, timestamps):
        hash_key = {"condition_hash": condition_hash}

        (
            rng_seed,
            duration,
            blue_green_saturation,
            pattern_width,
            pattern_aspect,
            temp_kernel,
            temp_bandwidth,
            ori_coherence,
            ori_fraction,
            ori_mix,
            num_directions,
        ) = (nda.Monet2() & hash_key).fetch1(
            "rng_seed",
            "duration",
            "blue_green_saturation",
            "pattern_width",
            "pattern_aspect",
            "temp_kernel",
            "temp_bandwidth",
            "ori_coherence",
            "ori_fraction",
            "ori_mix",
            "n_dirs",
        )

        monet2_table.add_interval(
            condition_hash=condition_hash,
            start_time=times[0],
            stop_time=times[1],
            rng_seed=rng_seed,
            duration=duration,
            blue_green_saturation=blue_green_saturation,
            pattern_width=pattern_width,
            pattern_aspect=pattern_aspect,
            temp_kernel=temp_kernel,
            temp_bandwidth=temp_bandwidth,
            ori_coherence=ori_coherence,
            ori_fraction=ori_fraction,
            ori_mix=ori_mix,
            num_directions=num_directions,
        )

    nwb.add_time_intervals(monet2_table)
