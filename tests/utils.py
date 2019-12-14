"""
Utilies common to multiple tests.

Andrew DeOrio <awdeorio@umich.edu>
"""

# Python 2 pathlib support requires backport
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path


# Directories containing test input files
TESTDIR = Path(__file__).resolve().parent
TESTDATA = TESTDIR / "testdata"
