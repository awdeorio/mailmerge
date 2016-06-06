"""
This test runs the mailmerge command line utility in a shell and diffs the
output.
"""

import unittest

import os
import sys
import subprocess

CORRECT_OUTPUT = \
""">>> message 0
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


class MailmergeTestCase(unittest.TestCase):
    def test_local(self):
        """A basic test using the default options"""
        try:
            os.remove("mailmerge_database.csv") # HACK: need to use constants from package
        except OSError:
            pass

        try:
            os.remove("mailmerge_template.txt") # HACK: need to use constants from package
        except OSError:
            pass
        subprocess.check_call([sys.executable, "main.py", "--sample"])
        output = subprocess.check_output(
            [sys.executable, "main.py", "--dry-run", "--no-limit"],
            universal_newlines=True)
        self.assertEqual(output, CORRECT_OUTPUT)


if __name__ == '__main__':
    unittest.main()
