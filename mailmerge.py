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
import click

TEMPLATE_FILENAME = "mailmerge_email.txt"
DATABASE_FILENAME = "mailmerge_database.csv"
SENDMAIL = "sendmail"

def sendmail(message):
    """Send email message using UNIX sendmail utility"""
    proc = Popen([SENDMAIL, "-t", "-oi"], stdin=PIPE)
    stdout, stderr = proc.communicate(message)
    retval = proc.returncode
    if retval != 0:
        print ">>> Error: sendmail returned {}".format(retval)
        if stdout is not None:
            print stdout
        if stderr is not None:
            print stderr

def create_sample_input_files(template_filename, database_filename):
    """Create sample template email and database"""
    print "Creating sample template email {}".format(template_filename)
    with open(template_filename, "w") as template_file:
        template_file.write(
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
    print "Creating sample database {}".format(database_filename)
    with open(database_filename, "w") as database_file:
        database_file.write(
            'email,name,position\n'
            'awdeorio@gmail.com,"Drew DeOrio",17\n'
            )
    print "Edit these files, and then run mailmerge again"


@click.command()
@click.option('--pretend/--no-pretend', default=True, help="Don't send email, just print")
def main(pretend=True):
    """Top level mailmerge application"""

    # Banner
    print "mailmerge 0.1 | Andrew DeOrio | 2016"

    # Create a sample email template and database if there isn't one already
    if not os.path.exists(TEMPLATE_FILENAME) or \
           not os.path.exists(DATABASE_FILENAME):
        create_sample_input_files(TEMPLATE_FILENAME, DATABASE_FILENAME)
        sys.exit(1)

    # Read template
    with open(TEMPLATE_FILENAME, "r") as template_file:
        content = template_file.read()
        content += "\n"
        template = jinja2.Template(content)

    # Read CSV file database
    with open(DATABASE_FILENAME, "r") as database_file:
        reader = csv.DictReader(database_file)

        # Each row corresponds to one email message
        for i, row in enumerate(reader):
            print ">>> message {}".format(i)

            # Fill in template fields using fields from row of CSV file
            message = template.render(**row)
            print message

            # Send message
            if pretend:
                print ">>> prentended to send message.  Use --no-pretend to actually send messages."
            else:
                sendmail(message)
                print ">>> sent message"

if __name__ == "__main__":
    main()
