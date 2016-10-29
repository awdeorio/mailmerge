"""
This test runs the mailmerge command line utility in a shell and diffs the
output.
"""

import os
import sh
from mailmerge import \
     TEMPLATE_FILENAME_DEFAULT, \
     DATABASE_FILENAME_DEFAULT, \
     CONFIG_FILENAME_DEFAULT

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


def test():
    """A basic test using the default options"""

    # Remove input files, if they exist
    if os.path.exists(DATABASE_FILENAME_DEFAULT):
        os.remove(DATABASE_FILENAME_DEFAULT)
    if os.path.exists(TEMPLATE_FILENAME_DEFAULT):
        os.remove(TEMPLATE_FILENAME_DEFAULT)
    if os.path.exists(CONFIG_FILENAME_DEFAULT):
        os.remove(CONFIG_FILENAME_DEFAULT)

    # Object references local command
    mailmerge_cmd = sh.Command("./bin/mailmerge")

    # Create sample input files
    output = mailmerge_cmd("--sample")

    # Run executable on sample input files
    output = mailmerge_cmd("--dry-run", "--no-limit")

    # Check output
    assert output == CORRECT_OUTPUT

    # Clean up
    os.remove(TEMPLATE_FILENAME_DEFAULT)
    os.remove(DATABASE_FILENAME_DEFAULT)
    os.remove(CONFIG_FILENAME_DEFAULT)
