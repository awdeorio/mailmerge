"""
Command line interface implementation.

Andrew DeOrio <awdeorio@umich.edu>
"""
from __future__ import print_function
import sys
import socket
import configparser
import smtplib
import jinja2
import click
from .template_message import TemplateMessage
from .sendmail_client import SendmailClient
from .utils import MailmergeError

# Python 2 pathlib support requires backport
try:
    from pathlib2 import Path
except ImportError:
    from pathlib import Path

# Python 2 UTF8 support requires csv backport
try:
    from backports import csv
except ImportError:
    import csv


@click.command(context_settings={"help_option_names": ['-h', '--help']})
@click.version_option()  # Auto detect version from setup.py
@click.option(
    "--sample", is_flag=True, default=False,
    help="Create sample database, template email, and config",
)
@click.option(
    "--dry-run/--no-dry-run", default=True,
    help="Don't send email, just print (True)",
)
@click.option(
    "--limit", is_flag=False, default=1,
    help="Limit the number of messages (1)",
)
@click.option(
    "--no-limit", is_flag=True, default=False,
    help="Do not limit the number of messages",
)
@click.option(
    "--template", "template_path",
    default="mailmerge_template.txt",
    type=click.Path(),
    help="template email file name (mailmerge_template.txt)"
)
@click.option(
    "--database", "database_path",
    default="mailmerge_database.csv",
    type=click.Path(),
    help="database CSV file name (mailmerge_database.csv)",
)
@click.option(
    "--config", "config_path",
    default="mailmerge_server.conf",
    type=click.Path(),
    help="configuration file name (mailmerge_server.conf)",
)
def cli(sample, dry_run, limit, no_limit,
        database_path, template_path, config_path):
    """
    A simple, command line mail merge tool.

    For examples and formatting features, see:
    https://github.com/awdeorio/mailmerge
    """
    # We need an argument for each command line option.  That also means a lot
    # of local variables.
    # pylint: disable=too-many-arguments, too-many-locals

    # Convert paths from string to Path objects
    # https://github.com/pallets/click/issues/405
    template_path = Path(template_path)
    database_path = Path(database_path)
    config_path = Path(config_path)

    check_input_files(template_path, database_path, config_path, sample)

    # No limit is an alias for limit=-1
    if no_limit:
        limit = -1

    try:
        template_message = TemplateMessage(template_path)
        csv_database = read_csv_database(database_path)
        sendmail_client = SendmailClient(config_path, dry_run)
        for i, row in enumerate_limit(csv_database, limit):
            sender, recipients, message = template_message.render(row)
            sendmail_client.sendmail(sender, recipients, message)
            print(">>> message {}".format(i))
            print(message.as_string())
            for filename in get_attachment_filenames(message):
                print(">>> attached {}".format(filename))
            print(">>> sent message {}".format(i))
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
        print(">>> Error reading config file {}: {}".format(config_path, err))
        sys.exit(1)
    except smtplib.SMTPException as err:
        print(">>> Error sending message", err, sep=' ', file=sys.stderr)
        sys.exit(1)
    except socket.error:
        print(">>> Error connecting to server")
        sys.exit(1)
    except MailmergeError as err:
        print(">>> {}".format(err))

    # Hints for user
    if not no_limit:
        print(">>> Limit was {} messages.  ".format(limit) +
              "To remove the limit, use the --no-limit option.")
    if dry_run:
        print((">>> This was a dry run.  "
               "To send messages, use the --no-dry-run option."))


if __name__ == "__main__":
    # No value for parameter, that's how click works
    # pylint: disable=no-value-for-parameter
    cli()


def check_input_files(template_path, database_path, config_path, sample):
    """Check if input files are present and hint the user."""
    if sample:
        create_sample_input_files(
            template_path,
            database_path,
            config_path,
        )
        sys.exit(0)
    if not template_path.exists():
        print("Error: can't find template email " + template_path)
        print("Create a sample (--sample) or specify a file (--template)")
        sys.exit(1)
    if not database_path.exists():
        print("Error: can't find database_path " + database_path)
        print("Create a sample (--sample) or specify a file (--database)")
        sys.exit(1)


def create_sample_input_files(template_path,
                              database_path,
                              config_path):
    """Create sample template email and database."""
    print("Creating sample template email {}".format(template_path))
    if template_path.exists():
        print("Error: file exists: " + template_path)
        sys.exit(1)
    with template_path.open("w") as template_file:
        template_file.write(
            u"TO: {{email}}\n"
            u"SUBJECT: Testing mailmerge\n"
            u"FROM: My Self <myself@mydomain.com>\n"
            u"\n"
            u"Hi, {{name}},\n"
            u"\n"
            u"Your number is {{number}}.\n"
        )
    print("Creating sample database {}".format(database_path))
    if database_path.exists():
        print("Error: file exists: " + database_path)
        sys.exit(1)
    with database_path.open("w") as database_file:
        database_file.write(
            u'email,name,number\n'
            u'myself@mydomain.com,"Myself",17\n'
            u'bob@bobdomain.com,"Bob",42\n'
        )
    print("Creating sample config file {}".format(config_path))
    if config_path.exists():
        print("Error: file exists: " + config_path)
        sys.exit(1)
    with config_path.open("w") as config_file:
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


def read_csv_database(database_path):
    """Read database CSV file, providing one line at a time."""
    with database_path.open("r") as database_file:
        reader = csv.DictReader(database_file)
        for row in reader:
            yield row


def enumerate_limit(iterable, limit):
    """Enumerate iterable, stopping after limit iterations.

    When limit == -1, enumerate entire iterable.
    """
    for i, value in enumerate(iterable):
        if limit != -1 and i >= limit:
            return
        yield i, value


def get_attachment_filenames(message):
    """Return a list of attachment filenames."""
    if message.get_content_maintype() != "multipart":
        return []

    filenames = []
    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get_content_maintype() == "text":
            continue
        if part.get("Content-Disposition") == "inline":
            continue
        if part.get("Content-Disposition") is None:
            continue
        filenames.append(part.get_filename())
    return filenames
