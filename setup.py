import os
import re
from pathlib import Path

from setuptools import find_namespace_packages, setup

IS_FROZEN = os.environ.get("FROZEN_REQUIREMENTS") == "mbd_core"
FROZEN_VERSION = "+frozen" if IS_FROZEN else "+release"
REQUIREMENTS_FILE = "requirements.txt" if IS_FROZEN else "requirements.in"


def get_requirements(requirements_file):
    """Loads the requirements from a given file."""
    requirements_content = Path(requirements_file).read_text()
    # Substitutes local overrides with package names
    requirements_content = re.sub(
        r".*?file:.*#egg=([\d\w\.]+).*?\s",
        r"\1\n",
        requirements_content,
        flags=re.MULTILINE,
    )
    # Substitutes all comments with an empty string
    requirements = re.sub(
        r"#.*\n?", "\n", requirements_content, flags=re.MULTILINE
    ).splitlines()
    # Filters any empty strings
    return list(filter(bool, map(str.strip, requirements)))


setup(
    name="mbd_core",
    version="0.2.0" + FROZEN_VERSION,
    description="""mbd core packages.""",
    author="Yassine Landa",
    author_email="yl@mbd.xyz",
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

    install_requires=get_requirements(REQUIREMENTS_FILE),
    zip_safe=False,
)
