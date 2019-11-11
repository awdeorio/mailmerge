"""
Tests for helper functions.

Andrew DeOrio <awdeorio@umich.edu>
"""
import mailmerge.__main__


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
