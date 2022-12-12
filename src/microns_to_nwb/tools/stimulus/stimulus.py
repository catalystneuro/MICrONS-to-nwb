import numpy as np
from hdmf.backends.hdf5 import H5DataIO
from phase3 import nda
from pynwb.image import OpticalSeries


def add_stimulus(scan_key, nwb, timestamps):
    movie = (nda.Stimulus & scan_key).fetch1("movie")
    # The movie dimensions are (height, width, number of frames), for NWB it should be
    # transposed to (number of frames, width, height)
    movie_transposed = movie.transpose(2, 1, 0)
    optical_series = OpticalSeries(
        name="visual stimulus",
        description="The visual stimulus is composed of natural movies ~30 fps in grayscale format.",
        distance=np.nan,  # unknown
        field_of_view=[np.nan, np.nan],
        orientation="0 is up",
        data=H5DataIO(movie_transposed, compression=True),
        timestamps=H5DataIO(timestamps, compression=True),
        unit="n.a.",
    )

    nwb.add_stimulus(optical_series)
