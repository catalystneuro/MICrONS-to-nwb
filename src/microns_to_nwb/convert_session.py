import os
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
from tools.intervals import add_trials
from tools.nwb_helpers import start_nwb
from tools.ophys import add_ophys
from tools.times import get_stimulus_times, get_frame_times, get_trial_times

from micronsnwbconverter import MICrONSNWBConverter
from tools.behavior import find_earliest_timestamp, add_eye_tracking, add_treadmill


def convert_session(
    nwbfile_path: str,
    ophys_file_path: str,
    ophys_timestamps_file_path: str,
    stimulus_movie_file_path: str,
    stimulus_movie_timestamps_file_path: str,
    trial_timestamps_file_path: str,
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

    # Fetch v8 timestamps from the pickle files
    movie_times = get_stimulus_times(scan_key=scan_key, file_path=stimulus_movie_timestamps_file_path)
    frame_times = get_frame_times(scan_key=scan_key, file_path=ophys_timestamps_file_path)
    trial_times = get_trial_times(scan_key=scan_key, file_path=trial_timestamps_file_path)

    # Shifting times to earliest provided behavioral timestamp when necessary
    pupil_timestamps = (nda.RawManualPupil & scan_key).fetch1("pupil_times")
    treadmill_timestamps = (nda.RawTreadmill & scan_key).fetch1("treadmill_timestamps")

    earliest_timestamp_in_behavior = find_earliest_timestamp(
        behavior_timestamps_arrays=[pupil_timestamps, treadmill_timestamps],
    )
    if earliest_timestamp_in_behavior < 0:
        warn(
            "Writing behavior data to NWB with negative timestamps is not recommended,"
            f"times are shifted to the earliest behavioral timestamp by {abs(earliest_timestamp_in_behavior)} seconds."
        )
        pupil_timestamps = pupil_timestamps + abs(earliest_timestamp_in_behavior)
        treadmill_timestamps = treadmill_timestamps + abs(earliest_timestamp_in_behavior)
        frame_times = frame_times + abs(earliest_timestamp_in_behavior)
        movie_times = movie_times + abs(earliest_timestamp_in_behavior)
        trial_times["start_frame_time"] = trial_times["start_frame_time"] + abs(earliest_timestamp_in_behavior)
        trial_times["end_frame_time"] = trial_times["end_frame_time"] + abs(earliest_timestamp_in_behavior)

    # Create the NWBFile
    nwbfile = start_nwb(scan_key)
    # Add eye position and pupil radius
    add_eye_tracking(scan_key, nwbfile, timestamps=pupil_timestamps)
    # Add the velocity of the treadmill
    add_treadmill(scan_key, nwbfile, timestamps=treadmill_timestamps)
    # Add trials
    add_trials(scan_key, nwbfile, trial_times=trial_times)
    # Add fluorescence traces, image masks and summary images to NWB
    add_ophys(scan_key, nwbfile, timestamps=frame_times)

    if verbose:
        print("Behavior, trials, and Fluorescence traces are added from datajoint.")

    converter = MICrONSNWBConverter(source_data=source_data)
    metadata = converter.get_metadata()

    metadata["Behavior"]["Movies"][0].update(
        description="The visual stimulus is composed of natural movie clips ~60 fps.",
    )

    metadata["NWBFile"].update(
        session_start_time=nwbfile.session_start_time,
    )

    conversion_options = dict(
        Ophys=dict(stub_test=False),
        Video=dict(
            external_mode=False,
            timestamps=movie_times.tolist(),
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
    stimulus_movie_timestamps_file_path: str,
    ophys_timestamps_file_path: str,
    trial_timestamps_file_path: str,
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
                        nwbfile_path=str(nwbfile_path),
                        ophys_file_path=str(ophys_file_path),
                        stimulus_movie_file_path=str(stimulus_movie_file_path),
                        stimulus_movie_timestamps_file_path=str(stimulus_movie_timestamps_file_path),
                        ophys_timestamps_file_path=str(ophys_timestamps_file_path),
                        trial_timestamps_file_path=str(trial_timestamps_file_path),
                        verbose=False,
                    )
                )
            for future in as_completed(futures):
                future.result()
                progress_bar.update(1)


if __name__ == "__main__":
    # Source data file paths
    # The list of file paths to the imaging data
    file_paths = [
        Path("/home/jovyan/microns/functional_scan_17797_4_7_v2.tif"),
    ]
    # The list of file paths to the stimulus movie files
    movie_file_paths = [
        "/Volumes/t7-ssd/microns/stimulus_17797_4_7_v4.avi",
    ]

    # The file path to the imaging timestamps pickle file (from v8 version)
    timestamps_file_path = Path(__file__).parent / "CatalystNeuroFileShare/ScanTimes.pkl"
    # The file path to the movie timestamps pickle file (from v8 version)
    movie_timestamps_file_path = Path(__file__).parent / "CatalystNeuroFileShare/v8_movie_timestamps.pkl"
    # The file path to the trials timestamps pickle file (from v8 version)
    trial_timestamps_file_path = Path(__file__).parent / "CatalystNeuroFileShare/Trial.pkl"

    # The file path to the NWB files
    nwb_output_path = Path("/home/jovyan/microns/nwbfiles/")
    nwbfile_list = [nwb_output_path / file_path.stem / f"{file_path.stem}.nwb" for file_path in file_paths]

    nwbfile_folder_paths = [nwb_output_path / file_path.stem for file_path in file_paths]
    [os.makedirs(nwbfile_folder_path, exist_ok=True) for nwbfile_folder_path in nwbfile_folder_paths]

    # Run parallel conversion
    parallel_convert_sessions(
        num_parallel_jobs=len(file_paths),
        nwbfile_list=nwbfile_list,
        ophys_file_paths=file_paths,
        stimulus_movie_file_paths=movie_file_paths,
        stimulus_movie_timestamps_file_path=str(movie_timestamps_file_path),
        ophys_timestamps_file_path=str(timestamps_file_path),
        trial_timestamps_file_path=str(trial_timestamps_file_path),
    )
