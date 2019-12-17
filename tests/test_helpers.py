"""
Tests for helper functions.

Andrew DeOrio <awdeorio@umich.edu>
"""
import textwrap
import pytest
import mailmerge.__main__

# Python 2 pathlib support requires backport
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

# Python 2 UTF8 support requires csv backport
try:
    from backports import csv
except ImportError:
    import csv


def test_enumerate_limit_no_limit():
    """Verify limit=-1 results in no early termination."""
    iterations = 0
    for _, _ in mailmerge.__main__.enumerate_limit(["a", "b", "c"], -1):
        iterations += 1
    assert iterations == 3


def test_enumerate_limit_values():
    """Verify limit=-1 results in no early termination."""
    values = ["a", "b", "c"]
    for i, value in mailmerge.__main__.enumerate_limit(values, -1):
        assert value == values[i]


def test_enumerate_limit_stop_early():
    """Verify limit results in early termination."""
    iterations = 0
    for _, _ in mailmerge.__main__.enumerate_limit(["a", "b", "c"], 2):
        iterations += 1
    assert iterations == 2


def test_enumerate_limit_zero():
    """Verify limit results in early termination."""
    iterations = 0
    for _, _ in mailmerge.__main__.enumerate_limit(["a", "b", "c"], 0):
        iterations += 1
    assert iterations == 0


def test_bad_csv(tmpdir):
    """Bad CSV includes includes filename and line number."""
    # CSV with unmatched quote
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        a,b
        1,"2
    """))

    # Force CSV strict mode by overwriting default 'excel' dialect
    csv.unregister_dialect('excel')
    csv.register_dialect('excel', strict=True)

    # The first line of data triggers an error
    with pytest.raises(csv.Error) as err:
        next(mailmerge.__main__.read_csv_database(database_path))
