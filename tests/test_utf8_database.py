"""Test mailmerge UTF8 compatibility in database / email addresses."""
import os
import unittest
import mailmerge


class TestUTF8Database(unittest.TestCase):
    """Test mailmerge UTF8 compatibility in database / email addresses."""

    def setUp(self):
        """Change directory to tests/ before any unit test."""
        os.chdir(os.path.dirname(__file__))

    def test_uft8_database(self):
        """Input email database with UTF8 email address."""
        # pylint: disable=no-self-use

        # Run executable on sample input files
        mailmerge.api.main(
            database_filename="test_utf8_database.database.csv",
            template_filename="test_utf8_database.template.txt",
            config_filename="server_dummy.conf",
            dry_run=False,
        )
