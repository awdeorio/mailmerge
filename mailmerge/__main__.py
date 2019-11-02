"""
Mail merge using CSV database and jinja2 template email.

Command line interface implementation.

Andrew DeOrio <awdeorio@umich.edu>
"""
import os
import io
import sys
import csv
import configparser
import smtplib
import jinja2
import click
import mailmerge.api


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
@click.option("--database", "database_filename",
              default=mailmerge.api.DATABASE_FILENAME_DEFAULT,
              help="database CSV file name; default " +
              mailmerge.api.DATABASE_FILENAME_DEFAULT)
@click.option("--template", "template_filename",
              default=mailmerge.api.TEMPLATE_FILENAME_DEFAULT,
              help="template email file name; default " +
              mailmerge.api.TEMPLATE_FILENAME_DEFAULT)
@click.option("--config", "config_filename",
              default=mailmerge.api.CONFIG_FILENAME_DEFAULT,
              help="configuration file name; default " +
              mailmerge.api.CONFIG_FILENAME_DEFAULT)
def cli(sample, dry_run, limit, no_limit,
        database_filename, template_filename, config_filename):
    """Command line interface."""
    # pylint: disable=too-many-arguments
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

    # No limit is an alias for limit=-1
    if no_limit:
        limit = -1

    try:
        mailmerge.api.main(
            dry_run=dry_run,
            limit=limit,
            database_path=database_filename,
            template_path=template_filename,
            config_path=config_filename,
        )
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
    except smtplib.SMTPException as err:
        print(">>> Error sending message", err, sep=' ', file=sys.stderr)

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
