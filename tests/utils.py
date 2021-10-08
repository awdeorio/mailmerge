"""
Utilies common to multiple tests.

Andrew DeOrio <awdeorio@umich.edu>
"""

from pathlib import Path


# Directories containing test input files
TESTDIR = Path(__file__).resolve().parent
TESTDATA = TESTDIR / "testdata"
