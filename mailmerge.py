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
            print "STDOUT:"
            print stdout
        if stderr is not None:
            print "STDERR:"
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
@click.option('--dry-run/--no-dry-run', default=True,
              help="Don't send email, just print")
@click.option('--limit', is_flag=False, default=1,
              help='Limit the number of messages; default 1')
@click.option('--no-limit', is_flag=True, default=False,
              help="Do not limit the number of messages")
def main(dry_run=True, limit=1, no_limit=False):
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
            if not no_limit and i >= limit:
                break

            print ">>> message {}".format(i)

            # Fill in template fields using fields from row of CSV file
            message = template.render(**row)
            print message

            # Send message
            if dry_run:
                print ">>> sent message DRY RUN"
            else:
                sendmail(message)
                print ">>> sent message"

    # Hints for user
    if not no_limit:
        print ">>> Limit was {} messages.  ".format(limit) + \
            "To remove the limit, use the --no-limit option."
    if dry_run:
        print ">>> This was a dry run.  To send messages, use --no-dry-run option."

if __name__ == "__main__":
    main()
