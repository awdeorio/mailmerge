"""Mailmerge build and install configuration."""
from pathlib import Path
import setuptools


# Read the contents of README file
PROJECT_DIR = Path(__file__).parent
README = PROJECT_DIR/"README.md"
LONG_DESCRIPTION = README.open().read()


setuptools.setup(
    name="mailmerge",
    description="A simple, command line mail merge tool",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    version="2.2.0",
    author="Andrew DeOrio",
    author_email="awdeorio@umich.edu",
    url="https://github.com/awdeorio/mailmerge/",
    license="MIT",
    packages=["mailmerge"],
    keywords=["mail merge", "mailmerge", "email"],
    install_requires=[
        "click",
        "configparser;python_version<'3.6'",
        "jinja2",
        "markdown",
        "html5"
    ],
    extras_require={
        "dev": [
            "pdbpp",
            "twine",
            "tox",
        ],
        "test": [
            "check-manifest",
            "codecov>=1.4.0",
            "freezegun",
            "pycodestyle",
            "pydocstyle",
            "pylint",
            "pytest",
            "pytest-cov",
            "pytest-mock",
            "sh",

            # Work around a dependency bug (I think) in pytest + python3.4
            "typing;python_version=='3.4'",
        ],
    },

    # Python command line utilities will be installed in a PATH-accessible bin/
    entry_points={
        "console_scripts": [
            "mailmerge = mailmerge.__main__:main",
        ]
    },
)
