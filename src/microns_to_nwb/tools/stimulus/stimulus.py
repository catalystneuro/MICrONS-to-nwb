import numpy as np
from hdmf.backends.hdf5 import H5DataIO
from phase3 import nda
from pynwb.image import OpticalSeries


def add_stimulus(scan_key, nwb):
    timestamps = (nda.FrameTimes() & scan_key).fetch1('frame_times')  # timestamps of stimulus images
    movie = (nda.Stimulus & scan_key).fetch1('movie')
    optical_series = OpticalSeries(
        name="visual stimulus",
        distance=np.nan,  # unknown
        field_of_view=[np.nan, np.nan],
        orientation="0 is up",
        data=H5DataIO(movie.transpose(2, 0, 1), compression=True),
        timestamps=H5DataIO(timestamps, compression=True),
        unit="n.a.",
    )

    nwb.add_stimulus(optical_series)
