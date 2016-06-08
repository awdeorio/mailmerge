"""
This test runs the mailmerge command line utility in a shell and diffs the
output.
"""

import os
import sh

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
    try:
        os.remove("mailmerge_database.csv") # HACK: need to use constants from package
    except OSError:
        pass

    try:
        os.remove("mailmerge_template.txt") # HACK: need to use constants from package
    except OSError:
        pass
    mailmerge_cmd = sh.Command("./bin/mailmerge")
    output = mailmerge_cmd("--sample")
    output = mailmerge_cmd("--dry-run", "--no-limit")
    assert output == CORRECT_OUTPUT
