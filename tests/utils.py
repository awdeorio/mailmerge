"""
Utilies common to multiple tests.

Andrew DeOrio <awdeorio@umich.edu>
"""
import os
import pathlib


# Directories containing test input files
TESTDIR = pathlib.Path(os.path.dirname(__file__))
TESTDATA = TESTDIR / "testdata"
