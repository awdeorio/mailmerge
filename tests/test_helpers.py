# coding=utf-8
# Python 2 source containing unicode https://www.python.org/dev/peps/pep-0263/
"""
Tests for helper functions.

Andrew DeOrio <awdeorio@umich.edu>
"""
import textwrap
import pytest
from mailmerge.__main__ import enumerate_range, read_csv_database
from mailmerge import MailmergeError

# Python 2 pathlib support requires backport
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

# Every test_enumerate_range_* unit test uses a list comprehension to yield all
# the values from the generator implementation.
# pylint: disable=unnecessary-comprehension


def test_enumerate_range_default():
    """Verify default start and stop."""
    output = [i for i in enumerate_range(["a", "b", "c"])]
    assert output == [(0, "a"), (1, "b"), (2, "c")]


def test_enumerate_range_stop_none():
    """Verify stop=None."""
    output = [i for i in enumerate_range(["a", "b", "c"], stop=None)]
    assert output == [(0, "a"), (1, "b"), (2, "c")]


def test_enumerate_range_stop_value():
    """Verify stop=value."""
    output = [i for i in enumerate_range(["a", "b", "c"], stop=1)]
    assert output == [(0, "a")]


def test_enumerate_range_stop_zero():
    """Verify stop=0."""
    output = [i for i in enumerate_range(["a", "b", "c"], stop=0)]
    assert output == []


def test_enumerate_range_stop_too_big():
    """Verify stop when value is greater than length."""
    output = [i for i in enumerate_range(["a", "b", "c"], stop=10)]
    assert output == [(0, "a"), (1, "b"), (2, "c")]


def test_enumerate_range_start_zero():
    """Verify start=0."""
    output = [i for i in enumerate_range(["a", "b", "c"], start=0)]
    assert output == [(0, "a"), (1, "b"), (2, "c")]


def test_enumerate_range_start_value():
    """Verify start=1."""
    output = [i for i in enumerate_range(["a", "b", "c"], start=1)]
    assert output == [(1, "b"), (2, "c")]


def test_enumerate_range_start_last_one():
    """Verify start=length - 1."""
    output = [i for i in enumerate_range(["a", "b", "c"], start=2)]
    assert output == [(2, "c")]


def test_enumerate_range_start_length():
    """Verify start=length."""
    output = [i for i in enumerate_range(["a", "b", "c"], start=3)]
    assert output == []


def test_enumerate_range_start_too_big():
    """Verify start past the end."""
    output = [i for i in enumerate_range(["a", "b", "c"], start=10)]
    assert output == []


def test_enumerate_range_start_stop():
    """Verify start and stop together."""
    output = [i for i in enumerate_range(["a", "b", "c"], start=1, stop=2)]
    assert output == [(1, "b")]


def test_csv_bad(tmpdir):
    """CSV with unmatched quote."""
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        a,b
        1,"2
    """))
    with pytest.raises(MailmergeError):
        next(read_csv_database(database_path))


def test_csv_quotes_commas(tmpdir):
    """CSV with quotes and commas.

    Note that quotes are escaped with double quotes, not backslash.
    https://docs.python.org/3.7/library/csv.html#csv.Dialect.doublequote
    """
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u'''\
        email,message
        one@test.com,"Hello, ""world"""
    '''))
    row = next(read_csv_database(database_path))
    assert row["email"] == u"one@test.com"
    assert row["message"] == 'Hello, "world"'


def test_csv_utf8(tmpdir):
    """CSV with quotes and commas."""
    database_path = Path(tmpdir/"database.csv")
    database_path.write_text(textwrap.dedent(u"""\
        email,message
        Laȝamon <lam@test.com>,Laȝamon emoji \xf0\x9f\x98\x80 klâwen
    """))
    row = next(read_csv_database(database_path))
    assert row["email"] == u"Laȝamon <lam@test.com>"
    assert row["message"] == u"Laȝamon emoji \xf0\x9f\x98\x80 klâwen"
