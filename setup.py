"""Mailmerge build and install configuration."""
from pathlib import Path
import setuptools


# Read the contents of README file
PROJECT_DIR = Path(__file__).parent
README = PROJECT_DIR/"README.md"
LONG_DESCRIPTION = README.open(encoding="utf8").read()


setuptools.setup(
    name="mailmerge",
    description="A simple, command line mail merge tool",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    version="2.2.2",
    author="Andrew DeOrio",
    author_email="awdeorio@umich.edu",
    url="https://github.com/awdeorio/mailmerge/",
    license="MIT",
    packages=["mailmerge"],
    keywords=["mail merge", "mailmerge", "email"],
    install_requires=[
        "click",
        "jinja2",
        "markdown",
        "html5lib"
    ],
    extras_require={
        "dev": [
            "pdbpp",
            "twine",
            "tox",
        ],
        "test": [
            "check-manifest",
            "freezegun",
            "pycodestyle",
            "pydocstyle",
            "pylint",
            "pytest",
            "pytest-cov",
            "pytest-mock",
        ],
    },
    python_requires='>=3.6',
    entry_points={
        "console_scripts": [
            "mailmerge = mailmerge.__main__:main",
        ]
    },
)
