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


def test_csv_bad(tmpdir):
    """Bad CSV includes includes filename and line number."""
    # CSV with unmatched quote
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        a,b
        1,"2
    """))

    # The first line of data triggers an error
    with pytest.raises(csv.Error):
        next(mailmerge.__main__.read_csv_database(database_path))


def test_csv_quotes_commas(tmpdir):
    """CSV with quotes and commas."""
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email,message
        one@test.com,"Hello, world"
    """))
    row = next(mailmerge.__main__.read_csv_database(database_path))
    assert row["email"] == u"one@test.com"
    assert row["message"] == "Hello, world"


def test_csv_utf8(tmpdir):
    """CSV with quotes and commas."""
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email,message
        Laȝamon <lam@test.com>,Laȝamon emoji \xf0\x9f\x98\x80 klâwen
    """))
    row = next(mailmerge.__main__.read_csv_database(database_path))
    assert row["email"] == u"Laȝamon <lam@test.com>"
    assert row["message"] == u"Laȝamon emoji \xf0\x9f\x98\x80 klâwen"
