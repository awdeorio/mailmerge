"""Mailmerge unit tests."""
import os
import sys
import shutil
import distutils.dir_util
import mailmerge


TEST_DIR = os.path.dirname(__file__)
TESTDATA_DIR = os.path.join(TEST_DIR, "testdata")


def create_and_clean_testdir(dirname):
    """Create temporary directory for test, if needed."""
    # Make sure tmp directory exists
    assert os.path.dirname(dirname) == "tmp"
    if not os.path.exists("tmp"):
        os.mkdir("tmp")

    # Remove stale directory
    if os.path.exists(dirname):
        shutil.rmtree(dirname)

    # Create directory for this test
    os.mkdir(dirname)


def test_stdout(capsys):
    """Verify stdout and stderr.

    pytest docs on capturing stdout and stderr
    https://pytest.readthedocs.io/en/2.7.3/capture.html
    """
    create_and_clean_testdir("tmp/test_simple")
    distutils.dir_util.copy_tree(
        os.path.join(TESTDATA_DIR, "test_simple"),
        "tmp/test_simple",
    )

    # Run mailmerge
    os.chdir("tmp/test_simple")
    mailmerge.api.main(no_limit=True)

    # Verify mailmerge output
    stdout, stderr = capsys.readouterr()
    assert stderr == ""
    assert ">>> message 0" in stdout
    assert ">>> sent message 0 DRY RUN" in stdout
    assert ">>> message 1" in stdout
    assert ">>> sent message 1 DRY RUN" in stdout
