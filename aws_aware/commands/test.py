"""
CLI - test commands
"""
import os
import click

from aws_aware.scriptconfig import CFG, RUNARGS, OUTPUT
from aws_aware.monitorclass import MonitorTasks
from aws_aware.compat import urlparse

# Local arguments for use with test sub-commands
TESTARGS = {}

@click.group()
@click.option('-awsprofile', '--awsprofile', help='If defined use the local AWS profile instead of id/secret.')
@click.option('-awsid', '--awsid')
@click.option('-awssecret', '--awssecret')
@click.option('-awsregion', '--awsregion')
@click.option('-emailrecipients', '--emailrecipients', help='Semi-colon separated list of email recipients for job status or other notifications.')
@click.option('-terse', '--terse', is_flag=True, default=False, help='Do not display headers in output')
@click.option('-verbose', '--verbose', is_flag=True, default=False, help='More verbose logging and output for some modules')
def test(**kwargs):
    """
    Script testing
    """
    # First get all of our common run args. If not passed in,
    #  they will be updated with global config values (if they line up)
    #  Then we look in the global config for explicit mappings (name differences) that exist

    OUTPUT.info('Merging common test arguments with global config file settings.', suppress=True)
    for key, val in RUNARGS.items():
        TESTARGS[key] = kwargs.pop(key, val)
        # Did we get an empty (unpassed) run argument?
        if TESTARGS[key] is None:
            # Do we have the same argument in CFG?
            if CFG.values.has_key(key):
                # Does it have a value? Great, lets use it
                if CFG.values[key] is not None:
                    TESTARGS[key] = CFG.values[key]

    suppressoutput = TESTARGS['terse'] or CFG.values.get('suppressconsoleoutput')
    OUTPUT.header('TESTING', suppress=suppressoutput)

@test.command('aws', help='Test AWS connectivity')
def aws():
    """
    Test AWS connectivity
    """
    OUTPUT.info('TEST: Validating AWS connectivity')

    try:
        monitortask = MonitorTasks(runargs=TESTARGS)
        OUTPUT.info('Testing AWS connectivity')
        monitortask.instantiate_aws()
        OUTPUT.echo('AWS Test Success!', color='green')

    except Exception as awsawareexception:
        raise awsawareexception

@test.command('awsdownload', help='Test AWS ability to download specific file')
@click.option('-sourcefile', '--sourcefile', help='File name to download from an s3 path (defined in the test arguments as -s3path')
@click.option('-destpath', '--destpath', help='Destination path/file to save download as.')
def awsdownload(sourcefile, destpath=None):
    """
    Test aws ability to download a specific file
    """
    OUTPUT.info('TEST: Validating aws file download ability')
    if destpath is None:
        destpath = os.path.join(os.path.abspath(os.path.curdir), sourcefile)
        OUTPUT.info('Using current directory and source file name as destination file path: {0}'.format(destpath))
    else:
        destpath = os.path.abspath(destpath)

    try:
        monitortask = MonitorTasks(runargs=TESTARGS)
        OUTPUT.info('Connecting to aws')
        monitortask.instantiate_aws()
        OUTPUT.echo('..Connected to AWS', color='green')
    except Exception as awsawareexception:
        raise awsawareexception

    s3fullfilepath = '{0}/{1}'.format(TESTARGS['s3path'], sourcefile)
    OUTPUT.info('Attempting to download file - {0}'.format(s3fullfilepath))
    s3url = urlparse(s3fullfilepath)
    downloaded = monitortask.aws.download_s3_file(
        bucket=s3url.netloc,
        path=s3url.path.lstrip('/'),
        destpath=destpath)

    if downloaded:
        OUTPUT.echo('..SUCCESS!', color='green')
    else:
        OUTPUT.echo('..FAILED!', color='red')
