"""
Mail merge using CSV database and jinja2 template email.

API implementation.

Andrew DeOrio <awdeorio@umich.edu>
"""
from __future__ import print_function
import os
import io
import sys
import smtplib
import configparser
import getpass
import datetime
# NOTE: Python 2.x UTF8 support requires csv and email backports
from backports import csv
import future.backports.email as email  # pylint: disable=useless-import-alias
import future.backports.email.parser  # pylint: disable=unused-import
import future.backports.email.utils  # pylint: disable=unused-import
import jinja2
import chardet
from . import smtp_dummy


# Configuration
TEMPLATE_FILENAME_DEFAULT = "mailmerge_template.txt"
DATABASE_FILENAME_DEFAULT = "mailmerge_database.csv"
CONFIG_FILENAME_DEFAULT = "mailmerge_server.conf"


def parsemail(raw_message):
    """Parse message headers, then remove BCC header."""
    message = email.parser.Parser().parsestr(raw_message)

    # Detect encoding
    detected = chardet.detect(bytearray(raw_message, "utf-8"))
    encoding = detected["encoding"]
    message.set_charset(encoding)
    print(">>> encoding {}".format(encoding))

    # Extract recipients
    addrs = email.utils.getaddresses(message.get_all("TO", [])) + \
        email.utils.getaddresses(message.get_all("CC", [])) + \
        email.utils.getaddresses(message.get_all("BCC", []))
    recipients = [x[1] for x in addrs]
    message.__delitem__("bcc")
    message.__setitem__('Date', email.utils.formatdate())
    text = message.as_string()
    sender = message["from"]
    return (text, sender, recipients)


def sendmail(text, sender, recipients, config_filename):
    """Send email message using Python SMTP library."""
    # Read config file from disk to get SMTP server host, port, username
    if not hasattr(sendmail, "host"):
        config = configparser.RawConfigParser()
        config.read(config_filename)
        sendmail.host = config.get("smtp_server", "host")
        sendmail.port = config.getint("smtp_server", "port")
        sendmail.username = config.get("smtp_server", "username")
        sendmail.security = config.get("smtp_server", "security")
        print(">>> Read SMTP server configuration from {}".format(
            config_filename))
        print(">>>   host = {}".format(sendmail.host))
        print(">>>   port = {}".format(sendmail.port))
        print(">>>   username = {}".format(sendmail.username))
        print(">>>   security = {}".format(sendmail.security))

    # Prompt for password
    if not hasattr(sendmail, "password"):
        if sendmail.security == "Dummy" or sendmail.username == "None":
            sendmail.password = None
        else:
            prompt = ">>> password for {} on {}: ".format(sendmail.username,
                                                          sendmail.host)
            sendmail.password = getpass.getpass(prompt)

    # Connect to SMTP server
    if sendmail.security == "SSL/TLS":
        smtp = smtplib.SMTP_SSL(sendmail.host, sendmail.port)
    elif sendmail.security == "STARTTLS":
        smtp = smtplib.SMTP(sendmail.host, sendmail.port)
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
    elif sendmail.security == "Never":
        smtp = smtplib.SMTP(sendmail.host, sendmail.port)
    elif sendmail.security == "Dummy":
        smtp = smtp_dummy.SMTP_dummy()
    else:
        raise configparser.Error("Unrecognized security type: {}".format(
            sendmail.security))

    # Send credentials
    if sendmail.username != "None":
        smtp.login(sendmail.username, sendmail.password)

    # Send message.  Note that we can't use the elegant
    # "smtp.send_message(message)" because that's python3 only
    smtp.sendmail(sender, recipients, text)
    smtp.close()


def create_sample_input_files(template_filename,
                              database_filename,
                              config_filename):
    """Create sample template email and database."""
    print("Creating sample template email {}".format(template_filename))
    if os.path.exists(template_filename):
        print("Error: file exists: " + template_filename)
        sys.exit(1)
    with io.open(template_filename, "w") as template_file:
        template_file.write(
            u"TO: {{email}}\n"
            u"SUBJECT: Testing mailmerge\n"
            u"FROM: My Self <myself@mydomain.com>\n"
            u"\n"
            u"Hi, {{name}},\n"
            u"\n"
            u"Your number is {{number}}.\n"
        )
    print("Creating sample database {}".format(database_filename))
    if os.path.exists(database_filename):
        print("Error: file exists: " + database_filename)
        sys.exit(1)
    with io.open(database_filename, "w") as database_file:
        database_file.write(
            u'email,name,number\n'
            u'myself@mydomain.com,"Myself",17\n'
            u'bob@bobdomain.com,"Bob",42\n'
        )
    print("Creating sample config file {}".format(config_filename))
    if os.path.exists(config_filename):
        print("Error: file exists: " + config_filename)
        sys.exit(1)
    with io.open(config_filename, "w") as config_file:
        config_file.write(
            u"# Example: GMail\n"
            u"[smtp_server]\n"
            u"host = smtp.gmail.com\n"
            u"port = 465\n"
            u"security = SSL/TLS\n"
            u"username = YOUR_USERNAME_HERE\n"
            u"#\n"
            u"# Example: Wide open\n"
            u"# [smtp_server]\n"
            u"# host = open-smtp.example.com\n"
            u"# port = 25\n"
            u"# security = Never\n"
            u"# username = None\n"
            u"#\n"
            u"# Example: University of Michigan\n"
            u"# [smtp_server]\n"
            u"# host = smtp.mail.umich.edu\n"
            u"# port = 465\n"
            u"# security = SSL/TLS\n"
            u"# username = YOUR_USERNAME_HERE\n"
            u"#\n"
            u"# Example: University of Michigan EECS Dept., with STARTTLS security\n"  # noqa: E501
            u"# [smtp_server]\n"
            u"# host = newman.eecs.umich.edu\n"
            u"# port = 25\n"
            u"# security = STARTTLS\n"
            u"# username = YOUR_USERNAME_HERE\n"
            u"#\n"
            u"# Example: University of Michigan EECS Dept., with no encryption\n"  # noqa: E501
            u"# [smtp_server]\n"
            u"# host = newman.eecs.umich.edu\n"
            u"# port = 25\n"
            u"# security = Never\n"
            u"# username = YOUR_USERNAME_HERE\n"
        )
    print("Edit these files, and then run mailmerge again")


def main(sample=False,
         dry_run=True,
         limit=1,
         no_limit=False,
         database_filename=DATABASE_FILENAME_DEFAULT,
         template_filename=TEMPLATE_FILENAME_DEFAULT,
         config_filename=CONFIG_FILENAME_DEFAULT):
    """Python API for mailmerge.

    mailmerge 0.1 by Andrew DeOrio <awdeorio@umich.edu>.

    A simple, command line mail merge tool.

    Render an email template for each line in a CSV database.
    """
    # pylint: disable=too-many-arguments,too-many-locals,too-many-branches
    # pylint: disable=too-many-statements
    # NOTE: this function needs a refactor, then remove ^^^
    # Create a sample email template and database if there isn't one already
    if sample:
        create_sample_input_files(
            template_filename,
            database_filename,
            config_filename,
        )
        sys.exit(0)
    if not os.path.exists(template_filename):
        print("Error: can't find template email " + template_filename)
        print("Create a sample (--sample) or specify a file (--template)")
        sys.exit(1)
    if not os.path.exists(database_filename):
        print("Error: can't find database_filename " + database_filename)
        print("Create a sample (--sample) or specify a file (--database)")
        sys.exit(1)

    try:
        # Read template
        with io.open(template_filename, "r") as template_file:
            content = template_file.read() + u"\n"
            template = jinja2.Template(content)

        # Read CSV file database
        database = []
        with io.open(database_filename, "r") as database_file:
            reader = csv.DictReader(database_file)
            for row in reader:
                database.append(row)

        # Each row corresponds to one email message
        for i, row in enumerate(database):
            if not no_limit and i >= limit:
                break

            print(">>> message {}".format(i))

            # Fill in template fields using fields from row of CSV file
            raw_message = template.render(**row)
            print(raw_message)

            # Parse message headers and detect encoding
            (text, sender, recipients) = parsemail(raw_message)

            # Send message
            if dry_run:
                print(">>> sent message {} DRY RUN".format(i))
            else:
                # Send message
                try:
                    sendmail(text, sender, recipients, config_filename)
                except smtplib.SMTPException as err:
                    print(">>> failed to send message {}".format(i))
                    timestamp = '{:%Y-%m-%d %H:%M:%S}'.format(
                        datetime.datetime.now()
                    )
                    print(timestamp, i, err, sep=' ', file=sys.stderr)
                else:
                    print(">>> sent message {}".format(i))

        # Hints for user
        if not no_limit:
            print(">>> Limit was {} messages.  ".format(limit) +
                  "To remove the limit, use the --no-limit option.")
        if dry_run:
            print((">>> This was a dry run.  "
                   "To send messages, use the --no-dry-run option."))

    except jinja2.exceptions.TemplateError as err:
        print(">>> Error in Jinja2 template: {}".format(err))
        sys.exit(1)
    except csv.Error as err:
        print(">>> Error reading CSV file: {}".format(err))
        sys.exit(1)
    except smtplib.SMTPAuthenticationError as err:
        print(">>> Authentication error: {}".format(err))
        sys.exit(1)
    except configparser.Error as err:
        print(">>> Error reading config file {}: {}".format(
            config_filename, err))
        sys.exit(1)
