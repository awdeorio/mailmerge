"""Test simple example inputs."""
import os
import unittest
import mailmerge

CORRECT_OUTPUT = u""">>> message 0
TO: myself@mydomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>

Hi, Myself,

Your number is 17.

>>> sent message 0 DRY RUN
>>> message 1
TO: bob@bobdomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>

Hi, Bob,

Your number is 42.

>>> sent message 1 DRY RUN
>>> This was a dry run.  To send messages, use the --no-dry-run option.
"""


class TestSimple(unittest.TestCase):
    """Simple tests of defaults."""
    def setUp(self):
        """Change directory to tests/ before any unit test."""
        os.chdir(os.path.dirname(__file__))

    def test(self):
        """A basic test using the default options"""
        # pylint: disable=no-self-use

        # Run executable on sample input files
        mailmerge.api.main(
            database_filename="test_simple.database.csv",
            template_filename="test_simple.template.txt",
            config_filename="server_dummy.conf",
            dry_run=True,
            no_limit=True,
        )
