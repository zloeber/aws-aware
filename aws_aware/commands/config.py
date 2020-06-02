"""
CLI - config commands
"""
import os
import click
from aws_aware.scriptconfig import Settings, CFG, OUTPUT

@click.group()
@click.option('--terse', is_flag=True, default=False, help='Do not display headers in output')
def config(terse):
    """
    Script configuration
    """
    suppressoutput = terse or CFG.values.get('suppressconsoleoutput')
    OUTPUT.header('SCRIPT CONFIGURATION', suppress=suppressoutput)


@config.command('show', help='Display the current configuration')
def show():
    """
    Show script configuration
    """
    for key, val in CFG.values.items():
        OUTPUT.configelement(name=key, value=val)


@config.command('path', help='Output the current configuration file path')
def path():
    """
    Display configuration file path
    """
    OUTPUT.configelement(name='Path', value=CFG.config_file)


@config.command('logpath', help='Output the current configuration log file path')
def logpath():
    """
    Output the current configuration log file path
    """
    OUTPUT.configelement(name='Path', value=CFG.get_logpath())


@config.command('get', help="Show a single configuration element.")
@click.argument('element')
def get(element):
    """
    Show a single configuration element.
    """
    if element in CFG.values:
        OUTPUT.configelement(name=element, value=CFG.values[element])


@config.command('change', help="Set a configuration element to value.")
@click.option('-whatif', '--whatif', default=False, is_flag=True,
              help='Displays what configuration parameters would get updated but does not update them.')
@click.argument('element', required=True)
@click.argument('value', required=True)
def change(whatif, element, value):
    """
    Set script configuration elements. These are saved for future script runs.
    """
    if element in CFG.values:
        if whatif:
            OUTPUT.info('Would have updated {0} to {1}'.format(CFG.values[element], value))
        else:
            OUTPUT.info('Updating {0} to {1}'.format(element, value))
            CFG.values[element] = value
            CFG.save()
    else:
        OUTPUT.error('No configuration element exists for {0}'.format(element))


@config.command('new', help="Create a default configuration file.")
@click.option('-filename', '--filename', help='Full path and name to configuration file (ie. c:\\temp\\config.yml)')
def new(filename):
    """
    Create a new global configuration file.
    """
    if filename is None:
        filename = os.path.join(os.path.abspath(os.path.curdir), 'config.yml')
    else:
        filename = os.path.abspath(filename)

    OUTPUT.info('Attempting to save new configuration file to: {0}'.format(filename))
    _newconfig = Settings()
    _newconfig.set_config_default_values()
    _newconfig.save_to_file(filename=filename)


@config.command('upgrade', help="Upgrade global configuration file with any new values. Maybe required after upgrading the module with pip.")
def upgrade():
    """
    Upgrade a global configuration file with any missing elements.
    """
    OUTPUT.info('Updating configuration file with any new global config options')
    CFG.merge_default_values()
    CFG.save()


@config.command('reset', help="Resets default values for any configuration element that are not an empty string by default. This includes log and job paths and could be useful for migrating a deployment between operating systems.")
def reset():
    """
    Resets default values for any configuration element that is not an empty string by default. This includes log and job paths and could be useful for migrating a deployment between operating systems.
    """
    OUTPUT.info('Resetting configuration file with default values.')
    CFG.reset_default_values()
    CFG.save()


@config.command('export', help="Exports configuration settings as commands.")
def export():
    """
    Exports configuration settings as commands.
    """
    for key, val in CFG.values.items():
        commandout = 'aws-aware -configfile {0} config change {1} {2}'.format(CFG.config_file, key, val)
        OUTPUT.info(commandout)
