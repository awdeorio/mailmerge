"""
Command line interface implementation.

Andrew DeOrio <awdeorio@umich.edu>
"""
from __future__ import print_function
import sys
import codecs
import textwrap
import click
from .template_message import TemplateMessage
from .sendmail_client import SendmailClient
from .exceptions import MailmergeError
from . import utils

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

# Python 2 UTF8 file redirection
# http://www.macfreek.nl/memory/Encoding_of_Python_stdout
if sys.stdout.encoding != 'UTF-8' and not hasattr(sys.stdout, "buffer"):
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout, 'strict')


@click.command(context_settings={"help_option_names": ['-h', '--help']})
@click.version_option()  # Auto detect version from setup.py
@click.option(
    "--sample", is_flag=True, default=False,
    help="Create sample template, database, and config",
)
@click.option(
    "--dry-run/--no-dry-run", default=True,
    help="Don't send email, just print (dry-run)",
)
@click.option(
    "--no-limit", is_flag=True, default=False,
    help="Do not limit the number of messages",
)
@click.option(
    "--limit", is_flag=False, default=1,
    type=click.IntRange(0, None),
    help="Limit the number of messages (1)",
)
@click.option(
    "--resume", is_flag=False, default=1,
    type=click.IntRange(1, None),
    help="Start on message number INTEGER",
)
@click.option(
    "--template", "template_path",
    default="mailmerge_template.txt",
    type=click.Path(),
    help="template email (mailmerge_template.txt)"
)
@click.option(
    "--database", "database_path",
    default="mailmerge_database.csv",
    type=click.Path(),
    help="database CSV (mailmerge_database.csv)",
)
@click.option(
    "--config", "config_path",
    default="mailmerge_server.conf",
    type=click.Path(),
    help="server configuration (mailmerge_server.conf)",
)
@click.option(
    "--output-format", "output_format",
    default="colorized",
    type=click.Choice(["colorized", "text", "raw"]),
    help="Output format (colorized).",
)
def main(sample, dry_run, limit, no_limit, resume,
         template_path, database_path, config_path,
         output_format):
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

    # Make sure input files exist and provide helpful prompts
    check_input_files(template_path, database_path, config_path, sample)

    # Calculate start and stop indexes.  Start and stop are zero-based.  The
    # input --resume is one-based.
    start = resume - 1
    stop = None if no_limit else resume - 1 + limit

    # Run
    message_num = 1 + start
    try:
        template_message = TemplateMessage(template_path)
        csv_database = read_csv_database(database_path)
        sendmail_client = SendmailClient(config_path, dry_run)
        for _, row in enumerate_range(csv_database, start, stop):
            sender, recipients, message = template_message.render(row)
            sendmail_client.sendmail(sender, recipients, message)
            print_bright_white_on_cyan(
                ">>> message {message_num}"
                .format(message_num=message_num),
                output_format,
            )
            print_message(message, output_format)
            print_bright_white_on_cyan(
                ">>> message {message_num} sent"
                .format(message_num=message_num),
                output_format,
            )
            message_num += 1
    except MailmergeError as error:
        hint_text = '\nHint: "--resume {}"'.format(message_num)
        sys.exit(
            "Error on message {message_num}\n"
            "{error}"
            "{hint}"
            .format(
                message_num=message_num,
                error=error,
                hint=(hint_text if message_num > 1 else ""),
            )
        )

    # Hints for user
    if not no_limit:
        print(
            ">>> Limit was {limit} message{pluralizer}.  "
            "To remove the limit, use the --no-limit option."
            .format(limit=limit, pluralizer=("" if limit == 1 else "s"))
        )
    if dry_run:
        print(
            ">>> This was a dry run.  "
            "To send messages, use the --no-dry-run option."
        )


if __name__ == "__main__":
    # No value for parameter, that's how click works
    # pylint: disable=no-value-for-parameter
    main()


def check_input_files(template_path, database_path, config_path, sample):
    """Check if input files are present and hint the user."""
    if sample:
        create_sample_input_files(template_path, database_path, config_path)
        sys.exit(0)

    if not template_path.exists():
        sys.exit(textwrap.dedent(u"""\
            Error: can't find template "{template_path}".

            Create a sample (--sample) or specify a file (--template).

            See https://github.com/awdeorio/mailmerge for examples.\
        """.format(template_path=template_path)))

    if not database_path.exists():
        sys.exit(textwrap.dedent(u"""\
            Error: can't find database "{database_path}".

            Create a sample (--sample) or specify a file (--database).

            See https://github.com/awdeorio/mailmerge for examples.\
        """.format(database_path=database_path)))

    if not config_path.exists():
        sys.exit(textwrap.dedent(u"""\
            Error: can't find config "{config_path}".

            Create a sample (--sample) or specify a file (--config).

            See https://github.com/awdeorio/mailmerge for examples.\
        """.format(config_path=config_path)))


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
            # Example: GMail
            [smtp_server]
            host = smtp.gmail.com
            port = 465
            security = SSL/TLS
            username = YOUR_USERNAME_HERE

            # Example: SSL/TLS
            # [smtp_server]
            # host = smtp.mail.umich.edu
            # port = 465
            # security = SSL/TLS
            # username = YOUR_USERNAME_HERE

            # Example: STARTTLS security
            # [smtp_server]
            # host = newman.eecs.umich.edu
            # port = 25
            # security = STARTTLS
            # username = YOUR_USERNAME_HERE

            # Example: No security
            # [smtp_server]
            # host = newman.eecs.umich.edu
            # port = 25
        """))
    print(textwrap.dedent(u"""\
        Created sample template email "{template_path}"
        Created sample database "{database_path}"
        Created sample config file "{config_path}"

        Edit these files, then run mailmerge again.\
    """.format(
        template_path=template_path,
        database_path=database_path,
        config_path=config_path,
    )))


def read_csv_database(database_path):
    """Read database CSV file, providing one line at a time.

    We'll use a class to modify the csv library's default dialect ('excel') to
    enable strict syntax checking.  This will trigger errors for things like
    unclosed quotes.
    """
    class StrictExcel(csv.excel):
        # Our helper class is really simple
        # pylint: disable=too-few-public-methods, missing-class-docstring
        strict = True

    with database_path.open(mode="r", encoding="utf-8") as database_file:
        reader = csv.DictReader(database_file, dialect=StrictExcel)
        try:
            for row in reader:
                yield row
        except csv.Error as err:
            raise MailmergeError(
                "{}:{}: {}".format(database_path, reader.line_num, err)
            )


def enumerate_range(iterable, start=0, stop=None):
    """Enumerate iterable, starting at index "start", stopping before "stop".

    To enumerate the entire iterable, start=0 and stop=None.
    """
    assert start >= 0
    assert stop is None or stop >= 0
    for i, value in enumerate(iterable):
        if i < start:
            continue
        if stop is not None and i >= stop:
            return
        yield i, value


def print_cyan(string, output_format):
    """Print string to stdout, optionally enabling color."""
    if output_format == "colorized":
        string = "\x1b[36m" + string + "\x1b(B\x1b[m"
    print(string)


def print_bright_white_on_cyan(string, output_format):
    """Print string to stdout, optionally enabling color."""
    if output_format == "colorized":
        string = "\x1b[7m\x1b[1m\x1b[36m" + string + "\x1b(B\x1b[m"
    print(string)


def print_message(message, output_format):
    """Print a message with colorized output."""
    assert output_format in ["colorized", "text", "raw"]

    if output_format == "raw":
        print(utils.flatten_message(message))
        return

    for header, value in message.items():
        print(u"{header}: {value}".format(header=header, value=value))
    print()
    for part in message.walk():
        if part.get_content_maintype() == "multipart":
            pass
        elif part.get_content_maintype() == "text":
            if message.is_multipart():
                # Only print message part dividers for multipart messages
                print_cyan(
                    ">>> message part: {content_type}"
                    .format(content_type=part.get_content_type()),
                    output_format,
                )
            charset = str(part.get_charset())
            print(part.get_payload(decode=True).decode(charset))
            print()
        elif is_attachment(part):
            print_cyan(
                ">>> message part: attachment {filename}"
                .format(filename=part.get_filename()),
                output_format,
            )
        else:
            print_cyan(
                ">>> message part: {content_type}"
                .format(content_type=part.get_content_type()),
                output_format,
            )


def is_attachment(part):
    """Return True if message part looks like an attachment."""
    return (
        part.get_content_maintype() != "multipart" and
        part.get_content_maintype() != "text" and
        part.get("Content-Disposition") != "inline" and
        part.get("Content-Disposition") is not None
    )
