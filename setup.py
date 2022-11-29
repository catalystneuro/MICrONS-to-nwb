# -*- coding: utf-8 -*-
from pathlib import Path

from setuptools import setup, find_packages

root = Path(__file__).parent
with open(root / "requirements.txt") as f:
    install_requires = f.readlines()

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="microns-to-nwb",
    version="1.0.0",
    description="NWB conversion scripts, functions, and classes for the MICrONS project.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ben Dichter, Cody Baker, and Szonja Weigl",
    author_email="ben.dichter@catalystneuro.com",
    url="https://github.com/catalystneuro/MICrONS-to-nwb",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    python_requires=">=3.7",
    install_requires=install_requires,
)
