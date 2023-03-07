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
        session_description=(
            "Contains calcium imaging recorded from multiple cortical visual areas "
            "and behavioral measurements while a mouse viewed natural movies and parametric stimuli. "
            "The structural ids are added as plane segmentation columns from the CAVE database on "
            f"{datetime.utcnow().strftime('%Y-%m-%d')}. "
            "To access the latest revision see the notebook that is linked to the dandiset. "
            "The structural ids might not be present for all plane segmentations."
        ),
        experiment_description=(
            "The light microscopic images were acquired from a cubic millimeter volume that "
            "spanned portions of primary visual cortex and three higher visual cortical areas. "
            "The volume was imaged in vivo by two-photon random access mesoscope (2P-RAM) from "
            "postnatal days P75 to P81 in a male mouse expressing a genetically encoded calcium "
            "indicator in excitatory cells, while the mouse viewed natural movies and parametric "
            "stimuli. The calcium imaging data includes the single-cell responses of an estimated "
            "75,000 pyramidal cells imaged over a volume of approximately 1200 x 1100 x 500 μm3 "
            "(anteroposterior x mediolateral x radial depth). The center of the volume was placed "
            "at the junction of primary visual cortex (VISp) and three higher visual areas, lateromedial"
            " area (VISlm), rostrolateral area (VISrl) and anterolateral area (VISal). During imaging, "
            "the animal was head-restrained, and the stimulus was presented to the left visual field. "
            "Treadmill rotation (single axis) and video of the animal's left eye were captured throughout "
            "the scan, yielding the locomotion velocity, eye movements, and pupil diameter data included here. "
            "The functional data were co-registered with electron microscopy (EM) data. The structural identifiers "
            "of the matched cells are added as plane segmentation columns extracted from the CAVE database. "
            "To access the latest revision see the notebook that is linked to this dandiset. The structural ids "
            "might not be present for all plane segmentations."
        ),
        subject=Subject(subject_id="17797", species="Mus musculus", age="P75D/P81D", sex="M"),
        session_start_time=datetime(2018, 3, int(scan_key["session"])),
        session_id=f"{scan_key['session']}-scan-{scan_key['scan_idx']}",
        related_publications="https://doi.org/10.1101/2021.07.28.454025",
    )
    return nwb
