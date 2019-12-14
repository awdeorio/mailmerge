"""
Utilies common to multiple tests.

Andrew DeOrio <awdeorio@umich.edu>
"""
import pathlib2 as pathlib


# Directories containing test input files
TESTDIR = pathlib.Path(__file__).resolve().parent
TESTDATA = TESTDIR / "testdata"
