from concurrent.futures import as_completed, ProcessPoolExecutor
from pathlib import Path
from warnings import warn

import datajoint as dj
from tqdm import tqdm

dj.config["database.host"] = "tutorial-db.datajoint.io"
dj.config["database.user"] = "microns"
dj.config["database.password"] = "microns2021"

from phase3 import nda

from convert_microns_to_nwb import build_nwb
from micronsnwbconverter import MICrONSNWBConverter
from tools.behavior import find_earliest_timestamp
from tools.stimulus import get_stimulus_movie_timestamps


def convert_session(
    ophys_file_path: str,
    stimulus_movie_file_paths: list,
    stimulus_movie_timestamps_file_path: str,
    nwbfile_path: str,
    verbose: bool = True,
):
    """Wrap converter for parallel execution."""

    scan_key = dict(
        session=Path(ophys_file_path).stem.split("_")[3],
        scan_idx=Path(ophys_file_path).stem.split("_")[4],
    )

    source_data = dict(
        Ophys=dict(file_path=ophys_file_path, scan_key=scan_key),
        Video=dict(file_paths=stimulus_movie_file_paths),
    )

    # Shifting times to earliest provided behavioral timestamp when necessary
    pupil_timestamps = (nda.RawManualPupil & scan_key).fetch1("pupil_times")
    treadmill_timestamps = (nda.RawTreadmill & scan_key).fetch1("treadmill_timestamps")

    earliest_timestamp_in_behavior = find_earliest_timestamp(
        behavior_timestamps_arrays=[pupil_timestamps, treadmill_timestamps],
    )
    stimulus_timestamps = get_stimulus_movie_timestamps(
        scan_key=scan_key,
        file_path=stimulus_movie_timestamps_file_path,
    )
    if verbose:
        print("Stimulus movie timestamps are reconstructed based on inter-trial times!")
    stimulus_timestamps += abs(earliest_timestamp_in_behavior)

    nwbfile = build_nwb(scan_key, time_offset=earliest_timestamp_in_behavior)
    if verbose:
        print("Behavior, trials, and Fluorescence traces are added from datajoint.")

    converter = MICrONSNWBConverter(source_data=source_data)
    metadata = converter.get_metadata()

    metadata["Behavior"]["Movies"][0].update(
        description="The visual stimulus is composed of natural movie clips ~60 fps.",
    )

    conversion_options = dict(
        Ophys=dict(stub_test=True),
        Video=dict(
            external_mode=True,
            timestamps=stimulus_timestamps.tolist(),
        ),
    )

    try:
        converter.run_conversion(
            nwbfile=nwbfile,
            nwbfile_path=nwbfile_path,
            metadata=metadata,
            conversion_options=conversion_options,
        )
        if verbose:
            print("Conversion successful.")

        return ophys_file_path

    except Exception as e:
        warn(f"There was an error during conversion. The source files are not removed. The full traceback: {e}")


def parallel_convert_sessions(
    num_parallel_jobs: int,
    nwbfile_list: list,
    ophys_file_paths: list,
    stimulus_movie_file_paths: list,
    stimulus_movie_timestamps_file_paths: list,
):
    with ProcessPoolExecutor(max_workers=num_parallel_jobs) as executor:
        with tqdm(total=len(ophys_file_paths), position=0, leave=False) as progress_bar:
            futures = []
            for nwbfile_path, ophys_file_path, stimulus_movie_file_path, stimulus_movie_timestamps_file_path in zip(
                nwbfile_list,
                ophys_file_paths,
                stimulus_movie_file_paths,
                stimulus_movie_timestamps_file_paths,
            ):
                futures.append(
                    executor.submit(
                        convert_session,
                        nwbfile_path=nwbfile_path,
                        ophys_file_path=str(ophys_file_path),
                        stimulus_movie_file_paths=[stimulus_movie_file_path],
                        stimulus_movie_timestamps_file_path=stimulus_movie_timestamps_file_path,
                        verbose=False,
                    )
                )
            for future in as_completed(futures):
                source_file_path = future.result()
                progress_bar.update(1)
                if source_file_path:
                    try:
                        Path(source_file_path).unlink()
                    except PermissionError:  # pragma: no cover
                        warn(f"Unable to clean up source file {source_file_path}! Please manually delete them.")