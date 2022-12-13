from phase3 import nda
from pynwb.epoch import TimeIntervals


def add_trials(scan_key, nwb, time_offset):

    # Add trials from "Trippy" stimulus type
    add_trials_from_trippy(nwb, scan_key=scan_key, time_offset=time_offset)
    # Add trials from "Clip" stimulus type
    add_trials_from_clip(nwb, scan_key=scan_key, time_offset=time_offset)
    # Add trials from "Monet2" stimulus type
    add_trials_from_monet2(nwb, scan_key=scan_key, time_offset=time_offset)


def add_trials_from_trippy(nwb, scan_key, time_offset):

    trippy_table = TimeIntervals(
        name="Trippy",
        description="The stimulus table for the cosine of a smoothened noise phase movie.",
    )

    trippy_columns = [
        ("stimulus_type", "The type of stimulus."),
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

    all_trial_data = ((nda.Trial & scan_key) * nda.Trippy).fetch(
        "trial_idx",
        "start_frame_time",
        "end_frame_time",
        "condition_hash",
        "type",
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
        order_by="trial_idx",
        as_dict=True,
    )

    for trial_data in all_trial_data:

        trippy_table.add_interval(
            id=trial_data["trial_idx"],
            start_time=trial_data["start_frame_time"] + time_offset,
            stop_time=trial_data["end_frame_time"] + time_offset,
            condition_hash=trial_data["condition_hash"],
            stimulus_type=trial_data["type"],
            rng_seed=trial_data["rng_seed"],
            texture_height=trial_data["tex_ydim"],
            texture_width=trial_data["tex_xdim"],
            duration=float(trial_data["duration"]),
            xnodes=trial_data["xnodes"],
            ynodes=trial_data["ynodes"],
            up_factor=trial_data["up_factor"],
            temp_freq=trial_data["temp_freq"],
            temp_kernel_length=trial_data["temp_kernel_length"],
            spatial_freq=trial_data["spatial_freq"],
        )

    nwb.add_time_intervals(trippy_table)


def add_trials_from_clip(nwb, scan_key, time_offset):

    clip_table = TimeIntervals(
        name="Clip",
        description="Composed of 10 second clips from cinematic releases, Sports-1M dataset, or custom rendered first person POV videos in 3D environment in Unreal Engine.",
    )

    clip_columns = [
        ("stimulus_type", "The type of stimulus."),
        ("condition_hash", "The hash for the stimulus condition."),
        ("movie_name", "The full clip source."),
        ("short_movie_name", "The type of the clip (cinematic, sports1m, rendered)."),
        ("duration", "The clip duration in seconds."),
    ]
    for column_name, column_description in clip_columns:
        clip_table.add_column(column_name, column_description)

    all_trial_data = ((nda.Trial & scan_key) * nda.Clip).fetch(
        "trial_idx",
        "start_frame_time",
        "end_frame_time",
        "condition_hash",
        "type",
        "movie_name",
        "short_movie_name",
        "duration",
        order_by="trial_idx",
        as_dict=True,
    )

    for trial_data in all_trial_data:

        clip_table.add_interval(
            id=trial_data["trial_idx"],
            start_time=trial_data["start_frame_time"] + time_offset,
            stop_time=trial_data["end_frame_time"] + time_offset,
            condition_hash=trial_data["condition_hash"],
            stimulus_type=trial_data["type"],
            movie_name=trial_data["movie_name"],
            short_movie_name=trial_data["short_movie_name"],
            duration=float(trial_data["duration"]),
        )

    nwb.add_time_intervals(clip_table)


def add_trials_from_monet2(nwb, scan_key, time_offset):

    monet2_table = TimeIntervals(
        name="Monet2",
        description="Generated from smoothened Gaussian noise and a global orientation and direction component.",
    )

    monet2_columns = [
        ("stimulus_type", "The type of stimulus."),
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
    ]
    for column_name, column_description in monet2_columns:
        monet2_table.add_column(column_name, column_description)

    all_trial_data = ((nda.Trial & scan_key) * nda.Monet2).fetch(
        "trial_idx",
        "start_frame_time",
        "end_frame_time",
        "condition_hash",
        "type",
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
        order_by="trial_idx",
        as_dict=True,
    )

    for trial_data in all_trial_data:

        monet2_table.add_interval(
            id=trial_data["trial_idx"],
            start_time=trial_data["start_frame_time"] + time_offset,
            stop_time=trial_data["end_frame_time"] + time_offset,
            condition_hash=trial_data["condition_hash"],
            stimulus_type=trial_data["type"],
            rng_seed=trial_data["rng_seed"],
            duration=float(trial_data["duration"]),
            blue_green_saturation=int(trial_data["blue_green_saturation"]),
            pattern_width=trial_data["pattern_width"],
            pattern_aspect=trial_data["pattern_aspect"],
            temp_kernel=trial_data["temp_kernel"],
            temp_bandwidth=float(trial_data["temp_bandwidth"]),
            ori_coherence=float(trial_data["ori_coherence"]),
            ori_fraction=trial_data["ori_fraction"],
            ori_mix=trial_data["ori_mix"],
            num_directions=trial_data["n_dirs"],
        )

    nwb.add_time_intervals(monet2_table)
