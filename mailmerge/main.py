"""
Mail merge using CSV database and jinja2 template email

Andrew DeOrio <awdeorio@umich.edu>
"""

import os
import sys
import smtplib
import email.parser
import ConfigParser #FIXME: not python3 compatible
from builtins import input  # for Python 2 and 3 compatibility
import getpass
import csv
import jinja2
import click


# Configuration
TEMPLATE_FILENAME_DEFAULT = "mailmerge_template.txt"
DATABASE_FILENAME_DEFAULT = "mailmerge_database.csv"
CONFIG_FILENAME_DEFAULT = "mailmerge_config.conf"


def sendmail(text, config_filename):
    """Send email message using Python SMTP library"""

    # Read config file from disk to get SMTP server host, port, username
    # FIXME: move config stuff out of this function?
    if not hasattr(sendmail, "host"):
        config = ConfigParser.RawConfigParser()
        config.read(config_filename)
        sendmail.host = config.get("smtp_server", "host")
        sendmail.port = config.get("smtp_server", "port")
        sendmail.username = config.get("smtp_server", "username")
        print(">>> Read SMTP server configuration from {}".format(config_filename))
        print(">>>   host = {}".format(sendmail.host))
        print(">>>   port = {}".format(sendmail.port))
        print(">>>   username = {}".format(sendmail.username))

    # Prompt for password
    if not hasattr(sendmail, "password"):
        sendmail.password = getpass.getpass(">>> password for {} on {}: ".format(
            sendmail.username, sendmail.host))

    # Parse message headers
    message = email.parser.Parser().parsestr(text)

    # Send message
    smtp = smtplib.SMTP_SSL(sendmail.host, sendmail.port)
    smtp.login(sendmail.username, sendmail.password)
    smtp.sendmail(
        message["from"],
        message["to"],
        message.as_string(),
        )
    smtp.close()

def create_sample_input_files(template_filename,
                              database_filename,
                              config_filename):
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
    print("Creating sample config file {}".format(config_filename))
    if os.path.exists(config_filename):
        print("Error: file exists: " + config_filename)
        sys.exit(1)
    with open(config_filename, "w") as config_file:
        config_file.write(
            '[smtp_server]\n'
            'host = smtp.gmail.com\n'
            'port = 465\n'
            'username = YOUR_USERNAME_HERE\n'
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
@click.option("--config", "config_filename",
              default=CONFIG_FILENAME_DEFAULT,
              help="configuration file name; default " + CONFIG_FILENAME_DEFAULT)
def main(sample=False,
         dry_run=True,
         limit=1,
         no_limit=False,
         database_filename=DATABASE_FILENAME_DEFAULT,
         template_filename=TEMPLATE_FILENAME_DEFAULT,
         config_filename=CONFIG_FILENAME_DEFAULT,
         ):
    #pylint: disable=too-many-arguments
    """mailmerge 0.1 by Andrew DeOrio <awdeorio@umich.edu>

    A simple, command line mail merge tool.

    Render an email template for each line in a CSV database.  Send messages
    with sendmail.
    """

    # Create a sample email template and database if there isn't one already
    if sample:
        create_sample_input_files(template_filename,
                                  database_filename,
                                  config_filename)
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
        try:
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
                    sendmail(message, config_filename)
                    print(">>> sent message {}".format(i))

            # Hints for user
            if not no_limit:
                print(">>> Limit was {} messages.  ".format(limit) +
                      "To remove the limit, use the --no-limit option.")
            if dry_run:
                print(">>> This was a dry run.  To send messages, use the --no-dry-run option.")

        except smtplib.SMTPAuthenticationError as e:
            print(">>> Authentication error: {}".format(e))
        except ConfigParser.Error as e:
            print(">>> Error reading config file {}: {}".format(
                config_filename, e))

if __name__ == "__main__":
    main()
