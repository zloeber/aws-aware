# -*- coding: utf-8 -*-

"""Console script for aws_aware."""
from __future__ import absolute_import, with_statement

import sys
import click
from aws_aware.scriptconfig import *

# Import all of our cli command groups
from aws_aware.commands.config import config as cli_config
from aws_aware.commands.run import run as cli_run


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'], max_content_width=120)

@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.version_option()
@click.option('-configfile', '--configfile', help='Load a custom configuration file')
def main(cmd=None, configfile=None):
    """
    Console script for aws-aware.
    """

    # If a configuration file was passed in then update it now
    if configfile is not None:
        try:
            CFG.configfile = configfile
            CFG.config_file = configfile
            CFG.get_emailhandler()
        except:
            OUTPUT.error('Unable to load configuration file - {0}'.format(configfile))
            sys.exit(1)

    try:
        ctx = click.get_current_context()
        if cmd:
            # Call command
            awsaware_cmd = cmd

        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())
            sys.exit(0)

    except Exception as e:
        # If we have an exception in our code then send a debug email if we can.
        OUTPUT.error(e.message)
        send_exception_email('exception')
        sys.exit(1)

    # Exit without errors.
#    sys.exit(0)

# Attach our command groups to our entry function
main.add_command(cli_config)
main.add_command(cli_run)


if __name__ == "__main__":
    main()