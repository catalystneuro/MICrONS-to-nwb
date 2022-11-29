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
        session_description="unknown",
        subject=Subject(subject_id="001", species="Mus musculus", age="P75D/P81D", sex="M"),
        session_start_time=datetime(1900, 1, 1),
        session_id=str(scan_key["session"]),
    )
    return nwb
