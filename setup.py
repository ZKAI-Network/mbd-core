import os
import re
from pathlib import Path

from setuptools import find_namespace_packages, setup

REQUIREMENTS_FILE = "requirements.txt"


setup(
    name="mbd_core",
    version="4",
    description="""recommenders packages.""",
    author="mbd ds team",
    author_email="na@mbd.xyz",
    python_requires="~=3.10",
    include_package_data=True,
    packages=find_namespace_packages(
        include=[
            "mbd_core",
            "mbd_core.*",
        ]
    ),
    package_data={
        "mbd_core.enrich.labelling": ["config.json"],
    },
    install_requires=Path(REQUIREMENTS_FILE).read_text().splitlines(),
    zip_safe=False,
)
