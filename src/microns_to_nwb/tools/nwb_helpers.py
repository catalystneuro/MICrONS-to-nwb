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
        session_start_time=datetime(1900, 1, 1),
        session_id=f"{scan_key['session']}_{scan_key['scan_idx']}",
        related_publications="https://doi.org/10.1101/2021.07.28.454025",
        experimenter=[
            "Bae, J. Alexander",
            "Baptiste, Mahaly",
            "Bodor, Agnes L.",
            "Brittain, Derrick",
            "Buchanan, JoAnn",
            "Bumbarger, Daniel J.",
            "Castro, Manuel A.",
            "Celii, Brendan",
            "Cobos, Erick",
            "Collman, Forrest",
            "Maçarico da Costa, Nuno",
            "Dorkenwald, Sven",
            "Elabbady, Leila",
            "G.Fahey Paul",
            "Fliss Tim",
            "Froudarakis Emmanouil",
            "Gager, Jay",
            "Gamlin, Clare",
            "Halageri, Akhilesh",
            "Hebditch, James",
            "Jia, Zhen",
            "Jordan, Chris",
            "Kapner, Daniel",
            "Kemnitz, Nico",
            "Kinn, Sam",
            "Koolman, Selden",
            "Kuehner, Kai",
            "Lee, Kisuk",
            "Li, Kai",
            "Lu, Ran",
            "Macrina, Thomas",
            "Mahalingam, Gayathri",
            "McReynolds, Sarah",
            "Miranda, Elanine",
            "Mitchell, Eric",
            "Mondal, Shanka Subhra",
            "Moorem Merlin",
            "Mu, Shang",
            "Muhammad, Taliah",
            "Nehoran, Barak",
            "Ogedengbe, Oluwaseun",
            "Papadopoulos, Christos",
            "Papadopoulos, Stelios",
            "Patel, Saumil",
            "Pitkow, Xaq",
            "Popovych, Sergiy",
            "Ramos, Anthony",
            "Reid, R.Clay",
            "Reimer, Jacob",
            "M.Schneider - Mizell, Casey",
            "Seung, H.Sebastian",
            "Silverman, Ben",
            "Silversmith, William",
            "Sterling, Amy",
            "Sinz, Fabian H.",
            "Smith, Cameron L.",
            "Suckow, Shelby",
            "Takeno, Marc",
            "Tan, Zheng H.",
            "Tolias, Andreas S.",
            "Torres, Russel",
            "Turner, Nicholas L.",
            "Edgar, Y.Walker",
            "Wang, Tianyu",
            "Williams, Grace",
            "Williams, Sarah",
            "Willie, Kyle",
            "Willie, Ryan",
            "Wong, William",
            "Wu, Jingpeng",
            "Xu, Chris",
            "Yang, Runzhe",
            "Yatsenko, Dimitri",
            "Ye, Fei",
            "Yin, Wenjing",
            "Yu, Szi - chieh",
        ]
    )
    return nwb
