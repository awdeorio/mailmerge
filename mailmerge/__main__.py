"""
Mail merge using CSV database and jinja2 template email.

Command line interface implementation.

Andrew DeOrio <awdeorio@umich.edu>
"""
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
    mailmerge.api.main(
        sample=sample,
        dry_run=dry_run,
        limit=limit,
        no_limit=no_limit,
        database_filename=database_filename,
        template_filename=template_filename,
        config_filename=config_filename,
    )


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    cli()
