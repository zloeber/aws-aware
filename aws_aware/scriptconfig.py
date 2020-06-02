# -*- coding: utf-8 -*-
from __future__ import absolute_import
from datetime import date
import os
import sys
import logging
import logging.handlers
import yaml
import figgypy

try:
    # Import as part of the aws_aware project
    from aws_aware.outputclass import OUTPUT
    from aws_aware.utility import Utility
    from aws_aware.smtplibrary import EmailNotification
except:
    # Otherwise import locally
    from outputclass import Output as outstream
    # Create our output pipeline (logging, screen handing)
    OUTPUT = outstream()
    from smtplibrary import EmailNotification
    from utility import Utility

# Allowed to be exported
__all__ = [
    'CFG',
    'EMAIL',
    'OUTPUT',
    'UTIL',
    'RUNARGS',
    'MONITORARGS',
    'send_exception_email']

# Script globals
SCRIPTPATH = os.path.abspath(os.path.split(__file__)[0])
CONFIGPATH = os.getenv('CONFIGFILE', os.path.join(SCRIPTPATH, ('config' + os.sep + 'default-config.yml')))
MONITORCONFIGPATH = os.getenv('MONITORCONFIGFILE', os.path.join(SCRIPTPATH, ('config' + os.sep + 'default-monitors.yml')))
DATAPATH = os.getenv('DATAPATH', os.path.join(SCRIPTPATH, ('config' + os.sep + 'instance_data.yml')))

# Common arguments for all run operations
RUNARGS = {
    'awsid': None,
    'awssecret': None,
    'awsregion': None,
    'awsprofile': None,
    'emailrecipients': None,
    'monitorconfig': MONITORCONFIGPATH,
    'terse': None,
    'verbose': None,
    'force': False,
    'datapath': None,
}

MONITORARGS = {
    # 'environment': None,
    # 'appname': None,
    # 'costcenter': None,
    'monitorconfig': MONITORCONFIGPATH,
    'includeundefined': False,
    'skipprobe': False,
    'sendwarnings': False,
    'sendalerts': False
}

DEFAULTAPPCONFIG = {
    'awsregion': 'us-east-1',
    'emailexceptions': False,
    'emailexceptionsrecipient': '',
    'emailexceptionssender': 'ScriptException@locahost',
    'emailrecipients': '',
    'emailsmtpserver': 'localhost',
    'emailsmtpserverport': 25,
    'emailstatussender': 'AWS-Aware Bot',
    'emailstatussenderaddress': 'Aws-aware-bot@localhost',
    'emailtemplatepath': 'config{0}templates'.format(os.sep),
    'monitorconfig': MONITORCONFIGPATH,
    'logfile': 'runtime.log',
    'logformat': '%(relativeCreated)6d %(threadName)s %(message)s',
    'loggingenabled': False,
    'loglevel': 'INFO',
    'logpath': 'logs{0}'.format(os.sep),
    'awsprofile': '',
    'awsid': '',
    'awssecret': '',
    'suppressconsoleoutput': False,
    'slack_notifications': False,
    'slack_webhooks': (),
    'datapath': DATAPATH
}

# Common utility functions
UTIL = Utility()

class CustomConfig(figgypy.Config):
    """
    A decorated version of figgypy.Config that adds the ability to save configuration
    files back to disk. Currently only yaml is supported/tested. ~Zach
    """

    def __init__(self, *args, **kwargs):
        # If a configtype was passed in use it, otherwise default to yml
        self._configtype = kwargs.pop('configtype', 'yml')

        # pass through all args to the base class init
        super(CustomConfig, self).__init__(*args, **kwargs)

    def save_to_file(self, configdata=None, filename=None, configtype=None):
        """Save config to a file"""
        if configtype is None:
            if self._configtype:
                configtype = self._configtype
            else:
                configtype = 'yml'

        if filename is None:
            if self.config_file:
                filename = self.config_file
            else:
                raise Exception(
                    'No filename for the configuration was passed!',
                    name='configfile',
                    path=__file__,
                )
        if configtype == 'yaml' or configtype == 'yml':
            with open(filename, 'wb') as outfile:
                # No data passed in, so dumping our own dictionary instead
                if configdata is None:
                    yaml.safe_dump(self.values, outfile, encoding='utf-8', allow_unicode=True, default_flow_style=False)
                else:
                    yaml.safe_dump(configdata, outfile, encoding='utf-8', allow_unicode=True, default_flow_style=False)

    def save(self):
        """Save config to a file"""
        self.save_to_file()

class Settings(CustomConfig):
    """
    A class that understands configurations provided to aws-aware through
    configuration files or runtime parameters. A signleton object
    ``aws_aware.conf.settings`` will be instantiated and used.

    The precedence for settings, listing from least to greatest, are:
        - defaults: Configuration default settings
        - global: Contents parsed from yaml file ``config/config.yml`` if exists.
        - parameter: Settings passed in via arguments
    """

    def __init__(self, *args, **kwargs):
        # Default global configuration settings for a project
        self.configdefaults = DEFAULTAPPCONFIG.copy()
        self.configfile = kwargs.pop('config_file', '')
        try:
            self.scriptpath = os.path.abspath(os.path.split(__file__)[0])
        except:
            self.scriptpath = ''

        if not self.configfile:
            self.configfile = os.path.join(self.scriptpath, ('config' + os.sep + 'config.yml'))

        # Initialize the data dictionary for the default settings
        self._defaults = {}
        for key, value in self.configdefaults.items():
            self._defaults[key] = value

        # If there is no default config file then lets try to create one
        if not os.path.isfile(self.configfile):
            OUTPUT.info('Unable to find config file - {0}, initializing a new default config file instead.'.format(self.configfile), suppress=True)
            with open(self.configfile, "wb") as cfgfile:
                cfgfile.write(yaml.safe_dump(self._defaults, encoding='utf-8', allow_unicode=True, default_flow_style=False))
            OUTPUT.info('File saved!')

        # pass through all args to the base class init along with our config file path
        kwargs['config_file'] = self.configfile
        super(Settings, self).__init__(*args, **kwargs)

        # Merge any default values that may be missing
        self.merge_default_values()
        self.emailhandler = self.get_emailhandler()

    def _get_relative_path(self, path):
        """Return a path if it exists, otherwise it checks the script relative
        path and returns it if it exists."""
        if os.path.isdir(path):
            return os.path.abspath(path)
        elif os.path.isdir(os.path.join(self.scriptpath, path)):
            return os.path.abspath(os.path.join(self.scriptpath, path))

    def get_emailhandler(self):
        """Updates the emailhandler object"""
        try:
            self.emailhandler = EmailNotification(
                smtphost=self.values['emailsmtpserver'],
                fromuser=self.values['emailstatussender'],
                fromemail=self.values['emailstatussenderaddress'],
                port=(25 if not self.values['emailsmtpserverport'] else self.values['emailsmtpserverport']),
                templatedir=self.get_emailtemplatepath())
        except Exception as configerr:
            raise Exception(configerr.message)

    def get_workingjobpath(self):
        """Path of job data files this script produces"""
        ourpath = self.values['workingjobpath']
        if self._get_relative_path(ourpath):
            return self._get_relative_path(ourpath)
        else:
            OUTPUT.warning('Not able to resolve the workingjobpath in your configuration file - {0}'.format(ourpath))
            return os.path.abspath(ourpath)

    def get_ansibletemplatepath(self):
        """Path of local ansible template files"""
        ourpath = self.values['ansibletemplatepath']
        if self._get_relative_path(ourpath):
            return self._get_relative_path(ourpath)
        else:
            OUTPUT.warning('Not able to resolve the ansibletemplatepath in your configuration file - {0}'.format(ourpath))
            return os.path.abspath(ourpath)

    def get_emailtemplatepath(self):
        """Path to Jinja email templates"""
        ourpath = self.values['emailtemplatepath']
        if self._get_relative_path(ourpath):
            return self._get_relative_path(ourpath)
        else:
            OUTPUT.warning('Not able to resolve the emailtemplatepath in your configuration file - {0}'.format(ourpath))
            return os.path.abspath(ourpath)

    def get_logpath(self):
        """Path to log files"""
        ourpath = self.values['logpath']
        if self._get_relative_path(ourpath):
            return self._get_relative_path(ourpath)
        else:
            OUTPUT.warning('Not able to resolve the logpath in your configuration file - {0}'.format(ourpath))
            return os.path.abspath(ourpath)

    def get_archivepath(self):
        """Path to old job data files"""
        ourpath = self.values['archivejobpath']
        if self._get_relative_path(ourpath):
            return self._get_relative_path(ourpath)
        else:
            OUTPUT.warning('Not able to resolve the archivejobpath in your configuration file - {0}'.format(ourpath))
            return os.path.abspath(ourpath)


    def load_config(self, configfile=None):
        """Load a configuration file"""
        if configfile is not None:
            self.config_file = configfile

    def load_config_from_environment(self):
        """Read config values from the environment if present.

        environment variables must start with 'EMR_'
        """
        kwargs = {}
        for key in self.configdefaults:
            env = 'EMR_' + key.upper()
            val = os.getenv(env, None)
            if val is not None:
                kwargs[key] = val
        return kwargs

    def set_config_default_values(self):
        """Reset configuration to default values"""
        for key, val in self.configdefaults.items():
            self.set_value(key, val)

    def merge_default_values(self):
        """Merge in default values if they don't already exist or are set to none"""
        OUTPUT.info('Updating existing configuration item that are not yet set to the default values.', suppress=True)
        for key, val in self.configdefaults.items():
            if self.get_value(key) is None:
                self.set_value(key, val)

    def reset_default_values(self):
        """Resets default values for paths or other elements which are not empty strings"""
        OUTPUT.info('Resetting path elements in the loaded configuration file.')
        for key, val in self.configdefaults.items():
            if val:
                self.set_value(key, val)

# The primary way to interact with settings is to simply hit the
# already constructed CFG object.
try:
    #OUTPUT.info('Attempting to load global config from {0}'.format(CONFIGPATH), suppress=True)
    CFG = Settings(config_file=CONFIGPATH)
    OUTPUT.suppress_console_output(suppress=CFG.values.get('suppressconsoleoutput'))
except:
    raise Exception('Error loading script configuration file: {0}'.format(CONFIGPATH))

# Supress output if the global config tells us to do so
OUTPUT.suppress_console_output(CFG.values.get('suppressconsoleoutput'))
""" 
try:
    # Create email notification handler
    EMAIL = EmailNotification(
        smtphost=CFG.values['emailsmtpserver'],
        fromuser=CFG.values['emailstatussender'],
        fromemail=CFG.values['emailstatussenderaddress'],
        port=(25 if not CFG.values['emailsmtpserverport'] else CFG.values['emailsmtpserverport']),
        templatedir=CFG.get_emailtemplatepath())
except Exception as configerr:
    raise Exception(configerr.message)
 """
EMAIL = CFG.emailhandler

## Additional functions for configuration error handling
def send_exception_email(emailtype):
    """
    If we decide to capture exceptions we can call
    this to send well formated emails out with
    error data and location in the script
    """
    if emailtype == 'exception':
        try:
            if CFG.values['emailexceptions'] and CFG.values['emailexceptionsrecipient']:
                import cgitb
                emaildata = {
                    "emailtitle": "EMR Script Exception Error",
                    "date": date.today().strftime('%d, %b %Y'),
                    "exceptionhtml": cgitb.html(sys.exc_info())
                }

                EMAIL.send_email_template(
                    jinjatemplate='email-html_exception',
                    jinjadata=emaildata,
                    subject="EMR Script Exception Error",
                    recipients=str(CFG.values['emailexceptionsrecipient']).split(';')
                )
        except:
            pass

# Setup our logger configuration
logger = logging.getLogger(OUTPUT._logger.name)
logger.setLevel(getattr(logging, CFG.values['loglevel']))

try:
    # If logging to disk is enabled then go ahead and set it up now
    if CFG.values['loggingenabled']:
        formatter = logging.Formatter(CFG.values['logformat'])
        filehandler = logging.handlers.RotatingFileHandler((os.path.join(CFG.get_logpath(), CFG.values['logfile'])), maxBytes=1000000, backupCount=5 )
        filehandler.setFormatter(formatter)
        logger.addHandler(filehandler)

except SystemExit as e:
    if (e.code == 0) or (e.message == 'Non-Exception') or (e.code == 'Non-Exception'):
        sys.exit(0)
    else:
        sys.exit(1)
except Exception as e:
    # If we have an exception in our code then ensure that any running job doesn't end up
    #  permanently 'In Progress'
    send_exception_email('exception')
    sys.exit(1)
