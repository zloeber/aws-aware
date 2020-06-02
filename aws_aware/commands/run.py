"""
All run tasks for this project
"""
#from __future__ import absolute_import
import click
from aws_aware.scriptconfig import CFG, RUNARGS, OUTPUT, SCRIPTPATH, UTIL
from aws_aware.monitorclass import MonitorTasks

# Import monitor subcommand group
from aws_aware.commands.monitor import monitor as monitor_subcommand

# Arguments common to all run commands
RUN_ARGS = RUNARGS.copy()


@click.group()
@click.option('-awsprofile', '--awsprofile', help='If defined use the local AWS profile instead of id/secret.')
@click.option('-awsid', '--awsid')
@click.option('-awssecret', '--awssecret')
@click.option('-awsregion', '--awsregion')
@click.option('-emailrecipients', '--emailrecipients', help='Semi-colon separated list of email recipients for job status or other notifications.')
@click.option('-terse', '--terse', is_flag=True, default=False, help='Do not display headers in output')
@click.option('-verbose', '--verbose', is_flag=True, default=False, help='More verbose logging and output for some modules')
@click.option('-force', '--force', is_flag=True, default=False, help='Send notices regardless if thresholds are met.')
@click.option('-datapath', '--datapath', help='Path to local instance data.')
@click.pass_context
def run(ctx, awsprofile=None, awsid=None, awsregion=None, emailrecipients=None, terse=False, verbose=False, force=False, datapath=None, **kwargs):
    """
    Run aws-aware actions
    """
    # First get all of our common run args. If not passed in,
    #  they will be updated with global config values (if they line up)
    #  Then we look in the global config for explict mappings
    #  (name differences) that exist
    OUTPUT.info('Merging common run arguments with global config file settings.', suppress=True)
    RUN_ARGS = RUNARGS.copy()
    for key, val in RUN_ARGS.items():
        RUN_ARGS[key] = kwargs.pop(key, val)
        # Did we get an empty (unpassed) run argument?
        if RUN_ARGS[key] is None:
            # Do we have the same argument in CFG?
            if CFG.values.has_key(key):
                # Does it have a value? Great, lets use it
                if CFG.values[key] is not None:
                    RUN_ARGS[key] = CFG.values[key]

    # Sanitize run args for Tibco's sake *sigh*
    #for key, val in RUN_ARGS.items():
    #    # if we get passed in '' or "" then convert to empty string
    #    if val == "''" or val == '""':
    #        RUN_ARGS[key] = ''
    #    # if we get passed in null or Null convert to None
    #    if val == 'null' or val == 'Null':
    #        RUN_ARGS[key] = None
    ctx = click.get_current_context()
    RUN_ARGS = UTIL.santize_arguments(RUN_ARGS)
    ctx.obj = RUN_ARGS

@run.command('export', help='Exports all raw instance data without any filtering. Useful for pre-caching.')
@click.pass_obj
def export(ctx):
    """
    Exports all raw instance data without any filtering. Useful for pre-caching.
    """
    run_args = ctx.copy()
    suppressoutput = run_args['terse'] or CFG.values.get('suppressconsoleoutput')
    OUTPUT.header('Check Thresholds', suppress=suppressoutput)

    # Load up default monitors and instantiate a task object
    monitortask = MonitorTasks(runargs=run_args)

    # Pull aws information
    try:
        OUTPUT.info('Polling AWS')
        monitortask.poll_instance_data()
    except Exception as monitorclassexception:
        raise monitorclassexception

run.add_command(monitor_subcommand)


#"""Download instance cost data and creates a report"""
#"""
#@run.command('cost_report', help='Download instance cost data and creates a report')
#def cost_report():
#    
#    suppressoutput = RUN_ARGS['terse'] or CFG.values.get('suppressconsoleoutput')
#    OUTPUT.header('Cost Report', suppress=suppressoutput)
#
#    test = UTIL.update_ec2_pricing_file()
#"""
