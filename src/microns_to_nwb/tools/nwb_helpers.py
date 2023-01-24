from datetime import datetime
from uuid import uuid4

from pynwb import NWBFile
from pynwb.file import Subject


def check_module(nwb, name, description=None):
    if name in nwb.processing:
        return nwb.processing[name]
    else:
        return nwb.create_processing_module(name, description or name)


def start_nwb(scan_key):
    nwb = NWBFile(
        identifier=str(uuid4()),
        session_description="Contains calcium imaging recorded from multiple cortical visual areas "
        "and behavioral measurements while a mouse viewed natural movies and parametric stimuli.",
        subject=Subject(subject_id="17797", species="Mus musculus", age="P75D/P81D", sex="M"),
        session_start_time=datetime(2018, 3, int(scan_key['session'])),
        session_id=f"{scan_key['session']}_{scan_key['scan_idx']}",
        related_publications="https://doi.org/10.1101/2021.07.28.454025",
    )
    return nwb
