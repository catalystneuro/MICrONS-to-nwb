import numpy as np
from hdmf.backends.hdf5 import H5DataIO
from phase3 import nda
from pynwb.image import OpticalSeries


def add_stimulus(scan_key, nwb):
    # The stimulus images were synchronized with field 1 frame times
    timestamps = (nda.FrameTimes() & scan_key).fetch1("frame_times")
    field_of_view = (nda.Field() & scan_key).fetch("um_height", "um_width", as_dict=True)[0]
    width_in_meters = field_of_view["um_width"] / 1e6
    height_in_meters = field_of_view["um_height"] / 1e6
    movie = (nda.Stimulus & scan_key).fetch1("movie")
    # The movie dimensions are (height, width, number of frames), for NWB it should be
    # transposed to (number of frames, width, height)
    movie_transposed = movie.transpose(2, 1, 0)
    optical_series = OpticalSeries(
        name="visual stimulus",
        description="The visual stimulus is composed of natural movies ~30 fps in grayscale format.",
        distance=np.nan,  # unknown
        field_of_view=[width_in_meters, height_in_meters],
        orientation="0 is up",
        data=H5DataIO(movie_transposed, compression=True),
        timestamps=H5DataIO(timestamps, compression=True),
        unit="n.a.",
    )

    nwb.add_stimulus(optical_series)
