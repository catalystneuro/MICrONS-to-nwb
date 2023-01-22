from neuroconv import NWBConverter
from neuroconv.datainterfaces import VideoInterface
from ophys import MicronsTiffImagingInterface


class MICrONSNWBConverter(NWBConverter):
    """Primary conversion class for the MICrONS data."""

    data_interface_classes = dict(
        Ophys=MicronsTiffImagingInterface,
        Video=VideoInterface,
    )

    def __init__(self, source_data):
        super().__init__(source_data)
