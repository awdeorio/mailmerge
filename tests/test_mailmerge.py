"""Mailmerge unit tests."""
import os
import mailmerge


TEST_DIR = os.path.dirname(__file__)
TESTDATA_DIR = os.path.join(TEST_DIR, "testdata")


def test_stdout(capsys):
    """Verify stdout and stderr.

    pytest docs on capturing stdout and stderr
    https://pytest.readthedocs.io/en/2.7.3/capture.html
    """
    mailmerge.api.main(
        database_filename=os.path.join(TESTDATA_DIR, "simple_database.csv"),
        template_filename=os.path.join(TESTDATA_DIR, "simple_template.txt"),
        config_filename=os.path.join(TESTDATA_DIR, "simple_server.conf"),
        no_limit=True,
    )

    # Verify mailmerge output
    stdout, stderr = capsys.readouterr()
    assert stderr == ""
    assert ">>> message 0" in stdout
    assert ">>> sent message 0 DRY RUN" in stdout
    assert ">>> message 1" in stdout
    assert ">>> sent message 1 DRY RUN" in stdout
