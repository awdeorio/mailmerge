"""Test mailmerge UTF8 compatibility."""
import os
import unittest
import mailmerge


class TestUTF8(unittest.TestCase):
    """Test mailmerge UTF8 compatibility."""

    def setUp(self):
        """Change directory to tests/ before any unit test."""
        os.chdir(os.path.dirname(__file__))

    def test_uft8(self):
        """Input email template with UTF8."""
        # pylint: disable=no-self-use

        # Run executable on sample input files
        mailmerge.api.main(
            database_filename="test_utf8.database.csv",
            template_filename="test_utf8.template.txt",
            config_filename="server_dummy.conf",
            dry_run=False,
        )
