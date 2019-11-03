"""
Mail merge using CSV database and jinja2 template email.

Command line interface implementation.

Andrew DeOrio <awdeorio@umich.edu>
"""
import os
import io
import sys
import csv
import socket
import configparser
import smtplib
import jinja2
import click
from . utils import sendall


@click.command(context_settings={"help_option_names": ['-h', '--help']})
@click.version_option()  # Auto detect version
@click.option("--sample", is_flag=True, default=False,
              help="Create sample database, template email, and config")
@click.option("--dry-run/--no-dry-run", default=True,
              help="Don't send email, just print")
@click.option("--limit", is_flag=False, default=1,
              help="Limit the number of messages; default 1")
@click.option("--no-limit", is_flag=True, default=False,
              help="Do not limit the number of messages")
@click.option("--database", "database_path",
              default="mailmerge_database.csv",
              help="database CSV file name; default mailmerge_database.csv ")
@click.option("--template", "template_path",
              default="mailmerge_template.txt",
              help="template email file name; default mailmerge_template.txt")
@click.option("--config", "config_path",
              default="mailmerge_server.conf",
              help="configuration file name; default mailmerge_server.conf")
def cli(sample, dry_run, limit, no_limit,
        database_path, template_path, config_path):
    """Command line interface."""
    # pylint: disable=too-many-arguments, too-many-branches
    if sample:
        create_sample_input_files(
            template_path,
            database_path,
            config_path,
        )
        sys.exit(0)
    if not os.path.exists(template_path):
        print("Error: can't find template email " + template_path)
        print("Create a sample (--sample) or specify a file (--template)")
        sys.exit(1)
    if not os.path.exists(database_path):
        print("Error: can't find database_path " + database_path)
        print("Create a sample (--sample) or specify a file (--database)")
        sys.exit(1)

    # No limit is an alias for limit=-1
    if no_limit:
        limit = -1

    try:
        send_messages_generator = sendall(
            database_path,
            template_path,
            config_path,
            limit,
            dry_run,
        )
        for _, _, message, i in send_messages_generator:
            print(">>> message {}".format(i))
            print(message.as_string())
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
        print(">>> Error reading config file {}: {}".format(
            config_path, err))
        sys.exit(1)
    except smtplib.SMTPException as err:
        print(">>> Error sending message", err, sep=' ', file=sys.stderr)
        sys.exit(1)
    except socket.error:
        print(">>> Error connecting to server")
        sys.exit(1)

    # Hints for user
    if not no_limit:
        print(">>> Limit was {} messages.  ".format(limit) +
              "To remove the limit, use the --no-limit option.")
    if dry_run:
        print((">>> This was a dry run.  "
               "To send messages, use the --no-dry-run option."))


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()


def create_sample_input_files(template_path,
                              database_path,
                              config_path):
    """Create sample template email and database."""
    print("Creating sample template email {}".format(template_path))
    if os.path.exists(template_path):
        print("Error: file exists: " + template_path)
        sys.exit(1)
    with io.open(template_path, "w") as template_file:
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
    if os.path.exists(database_path):
        print("Error: file exists: " + database_path)
        sys.exit(1)
    with io.open(database_path, "w") as database_file:
        database_file.write(
            u'email,name,number\n'
            u'myself@mydomain.com,"Myself",17\n'
            u'bob@bobdomain.com,"Bob",42\n'
        )
    print("Creating sample config file {}".format(config_path))
    if os.path.exists(config_path):
        print("Error: file exists: " + config_path)
        sys.exit(1)
    with io.open(config_path, "w") as config_file:
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
