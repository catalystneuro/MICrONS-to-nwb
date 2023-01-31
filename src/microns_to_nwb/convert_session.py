from concurrent.futures import as_completed, ProcessPoolExecutor
from pathlib import Path
from warnings import warn

from neuroconv.tools.data_transfers import automatic_dandi_upload
from nwbinspector import inspect_nwb
from nwbinspector.inspector_tools import format_messages, save_report
from tqdm import tqdm
import datajoint as dj

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
    stimulus_movie_file_path: str,
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
        Video=dict(file_paths=[stimulus_movie_file_path]),
    )

    # Shifting times to earliest provided behavioral timestamp when necessary
    pupil_timestamps = (nda.RawManualPupil & scan_key).fetch1("pupil_times")
    treadmill_timestamps = (nda.RawTreadmill & scan_key).fetch1("treadmill_timestamps")

    earliest_timestamp_in_behavior = find_earliest_timestamp(
        behavior_timestamps_arrays=[pupil_timestamps, treadmill_timestamps],
    )
    stimulus_movie_file_path = Path(stimulus_movie_file_path)
    timestamps_file_name = f"{stimulus_movie_file_path.stem}_timestamps.csv"
    stimulus_movie_timestamps_file_path = stimulus_movie_file_path.parent / timestamps_file_name
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
            external_mode=False,
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

        nwbfile_path = Path(nwbfile_path)
        # Run inspection for nwbfile
        results = list(inspect_nwb(nwbfile_path=nwbfile_path))
        report_path = nwbfile_path.parent / f"{nwbfile_path.stem}_report.txt"
        save_report(
            report_file_path=report_path,
            formatted_messages=format_messages(
                results,
                levels=["importance", "file_path"],
            ),
        )
        # Upload nwbfile to DANDI
        automatic_dandi_upload(
            dandiset_id="000402",
            nwb_folder_path=nwbfile_path.parent,
            cleanup=False,
        )

        if verbose:
            print("Cleaning up after successful upload to DANDI ...")
        Path(ophys_file_path).unlink()
        Path(stimulus_movie_file_path).unlink()

    except Exception as e:
        warn(f"There was an error during conversion. The source files are not removed. The full traceback: {e}")


def parallel_convert_sessions(
    num_parallel_jobs: int,
    nwbfile_list: list,
    ophys_file_paths: list,
    stimulus_movie_file_paths: list,
):
    with ProcessPoolExecutor(max_workers=num_parallel_jobs) as executor:
        with tqdm(total=len(ophys_file_paths), position=0, leave=False) as progress_bar:
            futures = []
            for nwbfile_path, ophys_file_path, stimulus_movie_file_path in zip(
                nwbfile_list,
                ophys_file_paths,
                stimulus_movie_file_paths,
            ):
                futures.append(
                    executor.submit(
                        convert_session,
                        nwbfile_path=nwbfile_path,
                        ophys_file_path=str(ophys_file_path),
                        stimulus_movie_file_path=stimulus_movie_file_path,
                        verbose=False,
                    )
                )
            for future in as_completed(futures):
                future.result()
                progress_bar.update(1)
