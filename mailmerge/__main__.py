"""
Command line interface implementation.

Andrew DeOrio <awdeorio@umich.edu>
"""
from __future__ import print_function
import sys
import socket
import configparser
import smtplib
import textwrap
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
    type=click.IntRange(0, None),
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
    Mailmerge is a simple, command line mail merge tool.

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
        sys.exit(">>> Error in Jinja2 template: {}".format(err))
    except csv.Error as err:
        sys.exit(">>> Error reading CSV file: {}".format(err))
    except smtplib.SMTPAuthenticationError as err:
        sys.exit(">>> Authentication error: {}".format(err))
    except configparser.Error as err:
        sys.exit(
            ">>> Error reading config file {filename}: {message}"
            .format(filename=config_path, message=err)
        )
    except smtplib.SMTPException as err:
        sys.exit(">>> Error sending message", err, sep=' ', file=sys.stderr)
    except socket.error:
        sys.exit(">>> Error connecting to server")
    except MailmergeError as err:
        sys.exit(">>> {}".format(err))

    # Hints for user
    if not no_limit:
        print(
            ">>> Limit was {} messages.  "
            "To remove the limit, use the --no-limit option."
            .format(limit)
        )
    if dry_run:
        print(
            ">>> This was a dry run.  "
            "To send messages, use the --no-dry-run option."
        )


if __name__ == "__main__":
    # No value for parameter, that's how click works
    # pylint: disable=no-value-for-parameter
    cli()


def check_input_files(template_path, database_path, config_path, sample):
    """Check if input files are present and hint the user."""
    if sample:
        create_sample_input_files(template_path, database_path, config_path)
        sys.exit(0)
    if not template_path.exists():
        sys.exit(
            "Error: can't find template {template_path}\n"
            "Create a sample (--sample) or specify a file (--template)\n"
            "\n"
            "See https://github.com/awdeorio/mailmerge for examples.\n"
            .format(template_path=template_path)
        )
    if not database_path.exists():
        sys.exit(
            "Error: can't find database {database_path}\n"
            "Create a sample (--sample) or specify a file (--database)\n"
            "\n"
            "See https://github.com/awdeorio/mailmerge for examples.\n"
            .format(database_path=database_path)
        )
    if not config_path.exists():
        sys.exit(
            "Error: can't find config {config_path}\n"
            "Create a sample (--sample) or specify a file (--config)\n"
            "\n"
            "See https://github.com/awdeorio/mailmerge for examples.\n"
            .format(config_path=config_path)
        )


def create_sample_input_files(template_path, database_path, config_path):
    """Create sample template, database and server config."""
    for path in [template_path, database_path, config_path]:
        if path.exists():
            sys.exit("Error: file exists: {}".format(path))
    with template_path.open("w") as template_file:
        template_file.write(textwrap.dedent(u"""\
            TO: {{email}}
            SUBJECT: Testing mailmerge
            FROM: My Self <myself@mydomain.com>
            
            Hi, {{name}},
            
            Your number is {{number}}.
        """))
    with database_path.open("w") as database_file:
        database_file.write(textwrap.dedent(u"""\
            email,name,number
            myself@mydomain.com,"Myself",17
            bob@bobdomain.com,"Bob",42
        """))
    with config_path.open("w") as config_file:
        config_file.write(textwrap.dedent(u"""\
            # Example: GMail, with SSL/TLS security
            [smtp_server]
            host = smtp.gmail.com
            port = 465
            security = SSL/TLS
            username = YOUR_USERNAME_HERE

            # Example: University of Michigan, with SSL/TLS security
            # [smtp_server]
            # host = smtp.mail.umich.edu
            # port = 465
            # security = SSL/TLS
            # username = YOUR_USERNAME_HERE

            # Example: University of Michigan EECS Dept., with STARTTLS security
            # [smtp_server]
            # host = newman.eecs.umich.edu
            # port = 25
            # security = STARTTLS
            # username = YOUR_USERNAME_HERE

            # Example: University of Michigan EECS Dept., with no security
            # [smtp_server]
            # host = newman.eecs.umich.edu
            # port = 25
        """))
    print("Created sample template email {}".format(template_path))
    print("Created sample database {}".format(database_path))
    print("Created sample config file {}".format(config_path))
    print("Edit these files, and then run mailmerge again")


def read_csv_database(database_path):
    """Read database CSV file, providing one line at a time."""
    # Modify the default dialect to be strict.  This will trigger errors for
    # things like unclosed quotes.
    class StrictExcel(csv.excel):
        """Strict version of default dialect."""

        # pylint: disable=too-few-public-methods
        strict = True

    # Open file and read using strict dialect
    with database_path.open("r") as database_file:
        reader = csv.DictReader(database_file, dialect=StrictExcel)
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
