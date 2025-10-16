import os
from pathlib import Path
from setuptools import find_namespace_packages, setup

REQUIREMENTS_FILE = "requirements.txt"
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="mbd_core",
    version="4.0.0",
    description="Common definitions for mbd recommender system.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="mbd ds team",
    author_email="na@mbd.xyz",
    python_requires="~=3.10",
    include_package_data=True,
    packages=find_namespace_packages(include=["mbd_core", "mbd_core.*"]),
    package_data={"mbd_core.enrich.labelling": ["config.json"]},
    install_requires=Path(REQUIREMENTS_FILE).read_text().splitlines(),
    license="MIT",
    url="https://mbd.xyz",
    zip_safe=False,
)
