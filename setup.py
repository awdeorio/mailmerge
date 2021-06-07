"""Mailmerge build and install configuration."""
import os
import io
import setuptools


# Read the contents of README file
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(PROJECT_DIR, "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()


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
        "backports.csv;python_version<'3.0'",
        "click",
        "configparser;python_version<'3.6'",

        # We mock the time when testing the rate limit feature
        "freezegun",

        # The attachments feature relies on a bug fix in the future library
        # https://github.com/awdeorio/mailmerge/pull/56
        "future>0.18.0",

        "jinja2",
        "markdown",
        "pathlib2;python_version<'3.6'",
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
            "mock;python_version<'3.0'",
            "pycodestyle",
            "pydocstyle",
            "pylint",
            "pytest",
            "pytest-cov",

            # Work around a dependency bug (I think) in pytest + python3.4
            "typing;python_version=='3.4'",

            "sh",
        ],
    },

    # Python command line utilities will be installed in a PATH-accessible bin/
    entry_points={
        "console_scripts": [
            "mailmerge = mailmerge.__main__:main",
        ]
    },
)
