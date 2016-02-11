#!/usr/bin/env python

"""
Mail merge using CSV database and jinja2 template email

Andrew DeOrio <awdeorio@umich.edu>
2016-02-10
"""

import os
import sys
import csv
from subprocess import Popen, PIPE
import jinja2

TEMPLATE_FILENAME = "mailmerge_email.txt" #FIXME option with default
DATABASE_FILENAME = "mailmerge_database.csv" #FIXME option with default
SENDMAIL = "sendmail"
PRETEND = True                     #FIXME option with default

def sendmail(message):
    """Send email message using UNIX sendmail utility"""
    p = Popen([SENDMAIL, "-t", "-oi"], stdin=PIPE)
    stdout, stderr = p.communicate(message)
    retval = p.returncode
    if retval != 0:
        print ">>> Error: sendmail returned {}".format(retval)
        if stdout is not None: print stdout
        if stderr is not None: print stderr
        print ">>> End error"

def create_sample_input_files():
    print "Creating sample template email {}".format(TEMPLATE_FILENAME)
    with open(TEMPLATE_FILENAME, "w") as fh:
        fh.write(
            "TO: {{email}}\n"
            "SUBJECT: Testing mailmerge\n"
            "FROM: Drew DeOrio <awdeorio@gmail.com>\n"
            "\n"
            "Hi, {{name}},\n"
            "\n"
            "Your position is {{position}}.\n"
            "\n"
            "AWD\n"
            )
    print "Creating sample database {}".format(DATABASE_FILENAME)
    with open(DATABASE_FILENAME, "w") as fh:
        fh.write(
            'email,name,position\n'
            'awdeorio@gmail.com,"Drew DeOrio",17\n'
            )
    print "Edit these files, and then run mailmerge again"

if __name__ == "__main__":
    
    # Banner
    print "mailmerge 0.1 | Andrew DeOrio | 2016"

    # Create a sample email template and database if there isn't one already
    if not os.path.exists(TEMPLATE_FILENAME) or \
           not os.path.exists(DATABASE_FILENAME):
        create_sample_input_files()
        sys.exit(1)

    # Read template
    with open(TEMPLATE_FILENAME, "r") as fh:
        content = fh.read()
        content += "\n"
        template = jinja2.Template(content)

    # Read CSV file database
    with open(DATABASE_FILENAME, "r") as fh:
        reader = csv.DictReader(fh)

        # Each row corresponds to one email message
        for i, row in enumerate(reader):
            print ">>> message {}".format(i)

            # Fill in template fields using fields from row of CSV file
            message = template.render(**row)
            print message
                
            # FIXME: add an option to enable actually sending the message
            if (PRETEND):
                print ">>> prentended to send message.  Use --nopretend to actually send messages."
            else:
                sendmail(message)
                print ">>> sent message"
