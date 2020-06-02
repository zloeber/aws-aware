"""
All monitor tasks for this project
"""
#from __future__ import absolute_import
import os
import click
from aws_aware.scriptconfig import CFG, MONITORARGS, OUTPUT, SCRIPTPATH, UTIL
from aws_aware.monitorclass import MonitorTasks

@click.group(invoke_without_command=True)
@click.option('-environment', '--environment', help='Application environment')
@click.option('-costcenter', '--costcenter', help='Cost center')
@click.option('-appname', '--appname', help='Application Name')
@click.option('-monitorconfig', '--monitorconfig', default=SCRIPTPATH + os.sep + 'config' + os.sep + 'default-monitor.yml', help='Path to YAML monitor definition file.')
@click.option('-skipprobe', '--skipprobe', is_flag=True, default=False, help='Skips reaching out to AWS to probe for data and uses existing cached data instead.')
@click.option('-includeundefined', '--includeundefined', is_flag=True, default=False, help='Instances not in your monitor set are are included and evaluated as zero threshold alerts')
@click.option('-sendwarnings', '--sendwarnings', is_flag=True, default=False, help='Send notices if the warning threshold has been reached.')
@click.option('-sendalerts', '--sendalerts', is_flag=True, default=False, help='Send notices if the alert threshold has been reached.')
@click.option('-reportname', '--reportname', default='threshold_report.html', help='Report filename. default is threshold_report.html')
@click.pass_context
def monitor(ctx, **kwargs):
    """
    Run threshold checks and sends notices if required/enabled.
    """
    clickcontext = click.get_current_context()
    run_args = clickcontext.parent.obj.copy()
    mon_args = MONITORARGS.copy()

    suppressoutput = run_args['terse'] or CFG.values.get('suppressconsoleoutput')

    OUTPUT.header('Check Thresholds', suppress=suppressoutput)
    OUTPUT.info('Merging common run arguments with global config file settings.', suppress=True)
    for key, val in MONITORARGS.items():
        mon_args[key] = kwargs.pop(key, val)
        # Did we get an empty (unpassed) run argument?
        if mon_args[key] is None:
            # Do we have the same argument in CFG?
            if CFG.values.has_key(key):
                # Does it have a value? Great, lets use it
                if CFG.values[key] is not None:
                    mon_args[key] = CFG.values[key]

    # Sanitize run args for Tibco's sake *sigh*
    mon_args = UTIL.santize_arguments(mon_args)

    if not clickcontext.invoked_subcommand:
        # Load up monitors and instantiate a task object
        monitortask = MonitorTasks(runargs=run_args, monargs=mon_args, monitorconfig=mon_args['monitorconfig'])

        try:
            OUTPUT.info('Polling AWS...')
            monitortask.poll_instance_data()
        except Exception as monitorclassexception:
            raise monitorclassexception

        # Update instance count information
        try:
            OUTPUT.info('Updating instance counts')
            monitortask.update_instance_counts()
        except Exception as monitorclassexception:
            raise monitorclassexception

        # Trigger any met thresholds
        try:
            OUTPUT.info('Checking of thresholds have been met')
            monitortask.check_threshold_triggers()
        except Exception as monitorclassexception:
            raise monitorclassexception

        # Send email notice if thresholds have been met anywhere
        try:
            OUTPUT.info('Sending email notices if required')
            monitortask.send_notice_with_report()
        except Exception as monitorclassexception:
            raise monitorclassexception
    else:
        OUTPUT.info('Invoking sub-command: {0}'.format(clickcontext.invoked_subcommand))
        ctx.obj = {
            'monargs':mon_args.copy(),
            'runargs':run_args.copy()
        }


@monitor.command('show', help='Show current monitors from definition file')
@click.pass_obj
def show(ctx):
    """
    Show current monitors
    """
    # This feels wrong...
    run_args = ctx['runargs']
    mon_args = ctx['monargs']

    suppressoutput = run_args['terse'] or CFG.values.get('suppressconsoleoutput')
    OUTPUT.header('Current Monitors', suppress=suppressoutput)
    MonitorTasks(monitorconfig=mon_args['monitorconfig']).show_monitors()

@monitor.command('report', help='Export instance data as html report')
@click.option('-filteredinstances', '--filteredinstances', default=False, is_flag=True, help='Report on filtered instances only. Default report includes all instances.')
@click.option('-reportname', '--reportname', default='index.html', help='Report filename. default is index.html')
@click.option('-email', '--email', is_flag=True, default=False, help='Sends an email of the report. Default is False.')
@click.pass_obj
def report(ctx, filteredinstances=False, reportname='index.html', email=False):
    """
    Export raw instance data as html report
    """
    run_args = ctx['runargs']
    mon_args = ctx['monargs']

    suppressoutput = run_args['terse'] or CFG.values.get('suppressconsoleoutput')
    OUTPUT.header('Export HTML Report', suppress=suppressoutput)

    # Load up monitors and instantiate a task object
    monitortask = MonitorTasks(runargs=run_args, monargs=mon_args, monitorconfig=mon_args['monitorconfig'])

    # Pull aws information
    try:
        OUTPUT.info('Polling instance data...')
        monitortask.poll_instance_data()
    except Exception as monitorclassexception:
        raise monitorclassexception

    # Update instance count information
    try:
        OUTPUT.info('Updating instance counts')
        monitortask.update_instance_counts()
    except Exception as monitorclassexception:
        raise monitorclassexception

    # Trigger any met thresholds
    try:
        OUTPUT.info('Checking of thresholds have been met')
        monitortask.check_threshold_triggers()
    except Exception as monitorclassexception:
        raise monitorclassexception

    # Update instance count information
    try:
        OUTPUT.info('Updating instance counts')
        monitortask.update_instance_counts()
    except Exception as monitorclassexception:
        raise monitorclassexception

    OUTPUT.info('Saving report (Filtered: {0}): {1}'.format(filteredinstances, reportname))
    monitortask.save_html_report(filteredinstances=filteredinstances, reportname=reportname)

    if email:
        OUTPUT.info('Sending report via email')
        monitortask.send_instance_report(filteredinstances=filteredinstances)


# @monitor.command('email_report', help='Email monitor instance report only.')
# @click.option('-filteredinstances', '--filteredinstances', default=False, is_flag=True,
#               help='Report on filtered instances only. Default report includes all instances.')
# @click.pass_obj
# @click.pass_context
# def email_report(ctx, filteredinstances=False):
#     """
#     Email monitor instance report only. Can optionally report on the instances filtered 
#     by monitor config filters.
#     """
#     run_args = ctx.copy()
#     suppressoutput = run_args['terse'] or CFG.values.get('suppressconsoleoutput')
#     OUTPUT.header('E-mail Report', suppress=suppressoutput)

#     # Load up monitors and instantiate a task object
#     monitortask = MonitorTasks(runargs=run_args, monitorconfig=mon_args['monitorconfig'], includeundefined=mon_args['includeundefined'])

#     try:
#         OUTPUT.info('Polling AWS...')
#         monitortask.poll_instance_data()
#     except Exception as monitorclassexception:
#         raise monitorclassexception

#     # Update instance count information
#     try:
#         OUTPUT.info('Updating instance counts')
#         monitortask.update_instance_counts()
#     except Exception as monitorclassexception:
#         raise monitorclassexception

#     # Trigger any met thresholds
#     try:
#         OUTPUT.info('Checking of thresholds have been met')
#         monitortask.check_threshold_triggers()
#     except Exception as monitorclassexception:
#         raise monitorclassexception

#     # Send email notice if thresholds have been met anywhere
#     try:
#         OUTPUT.info('Sending email notices if required')
#         monitortask.send_instance_report(filteredinstances=filteredinstances)
#     except Exception as monitorclassexception:
#         raise monitorclassexception


# @monitor.command('change', help="Set a configuration element to value.")
# @click.option('-whatif', '--whatif', default=False, is_flag=True,
#              help='Displays what configuration parameters would get updated but does not update them.')
# @click.argument('element', required=True)
# @click.argument('value', required=True)
# def change(whatif, name, element, value):
#    """
#    Set monitor configuration elements. These are saved for future script runs.
#    """