"""
Mail merge using CSV database and jinja2 template email

Andrew DeOrio <awdeorio@umich.edu>
"""

import os
import sys
import csv
from subprocess import Popen, PIPE
import jinja2
import click

TEMPLATE_FILENAME_DEFAULT = "mailmerge_template.txt"
DATABASE_FILENAME_DEFAULT = "mailmerge_database.csv"
SENDMAIL = "sendmail"

def sendmail(message):
    """Send email message using UNIX sendmail utility"""
    proc = Popen([SENDMAIL, "-t", "-oi"], stdin=PIPE, universal_newlines=True)
    stdout, stderr = proc.communicate(message)
    retval = proc.returncode
    if retval != 0:
        print(">>> Error: sendmail returned {}".format(retval))
        if stdout is not None:
            print("STDOUT:")
            print(stdout)
        if stderr is not None:
            print("STDERR:")
            print(stderr)

def create_sample_input_files(template_filename, database_filename):
    """Create sample template email and database"""
    print("Creating sample template email {}".format(template_filename))
    if os.path.exists(template_filename):
        print("Error: file exists: " + template_filename)
        sys.exit(1)
    with open(template_filename, "w") as template_file:
        template_file.write(
            "TO: {{email}}\n"
            "SUBJECT: Testing mailmerge\n"
            "FROM: My Self <myself@mydomain.com>\n"
            "\n"
            "Hi, {{name}},\n"
            "\n"
            "Your number is {{number}}.\n"
            )
    print("Creating sample database {}".format(database_filename))
    if os.path.exists(database_filename):
        print("Error: file exists: " + database_filename)
        sys.exit(1)
    with open(database_filename, "w") as database_file:
        database_file.write(
            'email,name,number\n'
            'myself@mydomain.com,"Myself",17\n'
            'bob@bobdomain.com,"Bob",42\n'
            )
    print("Edit these files, and then run mailmerge again")


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option("--sample", is_flag=True, default=False,
              help="Create sample database and template email files")
@click.option("--dry-run/--no-dry-run", default=True,
              help="Don't send email, just print")
@click.option("--limit", is_flag=False, default=1,
              help="Limit the number of messages; default 1")
@click.option("--no-limit", is_flag=True, default=False,
              help="Do not limit the number of messages")
@click.option("--database", "database_filename",
              default=DATABASE_FILENAME_DEFAULT,
              help="database CSV file name; default " + DATABASE_FILENAME_DEFAULT)
@click.option("--template", "template_filename",
              default=TEMPLATE_FILENAME_DEFAULT,
              help="template email file name; default " + TEMPLATE_FILENAME_DEFAULT)
def main(sample=False,
         dry_run=True,
         limit=1,
         no_limit=False,
         database_filename=DATABASE_FILENAME_DEFAULT,
         template_filename=TEMPLATE_FILENAME_DEFAULT):
    #pylint: disable=too-many-arguments
    """mailmerge 0.1 by Andrew DeOrio <awdeorio@umich.edu>

    A simple, command line mail merge tool.

    Render an email template for each line in a CSV database.  Send messages
    with sendmail.
    """

    # Create a sample email template and database if there isn't one already
    if sample:
        create_sample_input_files(template_filename, database_filename)
        sys.exit(0)
    if not os.path.exists(template_filename):
        print("Error: can't find template email " + template_filename)
        print("Create a sample with --sample or specify a file with --template")
        sys.exit(1)
    if not os.path.exists(database_filename):
        print("Error: can't find database_filename " + database_filename)
        print("Create a sample with --sample or specify a file with --database")
        sys.exit(1)

    # Read template
    with open(template_filename, "r") as template_file:
        content = template_file.read()
        content += "\n"
        template = jinja2.Template(content)

    # Read CSV file database
    with open(database_filename, "r") as database_file:
        reader = csv.DictReader(database_file)

        # Each row corresponds to one email message
        for i, row in enumerate(reader):
            if not no_limit and i >= limit:
                break

            print(">>> message {}".format(i))

            # Fill in template fields using fields from row of CSV file
            message = template.render(**row)
            print(message)

            # Send message
            if dry_run:
                print(">>> sent message {} DRY RUN".format(i))
            else:
                sendmail(message)
                print(">>> sent message {}".format(i))

    # Hints for user
    if not no_limit:
        print(">>> Limit was {} messages.  ".format(limit) +
              "To remove the limit, use the --no-limit option.")
    if dry_run:
        print(">>> This was a dry run.  To send messages, use the --no-dry-run option.")

if __name__ == "__main__":
    main()
