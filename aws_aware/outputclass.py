"""
Output to console or logfile in a centralized manner.
"""
import logging
import traceback
import click

__all__ = ['Output', 'OUTPUT']

class Output(object):
    """
    Class to centralize all output for a script. Uses click echo commands for pretty output
    (when not supressed). This also sends logs to a central system logger.
    """

    def __init__(self, loggername=__name__, loghandler=logging.NullHandler(), storelogs=True, suppress=False):
        self._logger = logging.getLogger(loggername)
        self._logger.addHandler(loghandler)
        self._log = []
        self._storelogs = storelogs
        self._suppress = suppress
        logging.captureWarnings(True)

    def suppress_console_output(self, suppress=None):
        """Suppress/Allow output to the screen"""
        if (suppress is not None) and isinstance(suppress, bool):
            self._suppress = suppress
        else:
            self._suppress = False

    def get_logs(self):
        """
        Return any stored logs.
        """
        return self._log

    def _add_log(self, mylog, logtype='info'):
        """
        Add a log
        """
        if logtype.lower() == 'error':
            self._logger.error(str(mylog))
        elif logtype.lower() == 'warning':
            self._logger.warning(str(mylog))
        elif logtype.lower() == 'debug':
            self._logger.debug(str(mylog))
        elif logtype.lower() == 'exception':
            self._logger.exception(str(mylog))
        else:   # Default to info logs
            self._logger.info(str(mylog))

        if self._storelogs:
            prepend = '{0}'.format(logtype.upper())
            self._log.append('{0}:{1}'.format(prepend, mylog))

    def info(self, text, suppress=None):
        """
        Add informational log
        """
        if suppress is None:
            suppress = self._suppress

        self._add_log(str(text), 'info')

        if not suppress:
            self.echo(text, color='white')

    def status(self, text, suppress=None):
        """
        Add a status log
        """
        if suppress is None:
            suppress = self._suppress
        self.info(text, suppress)
        self.line()

    def prompt(self, text, suppress=None):
        """
        Output prompt
        """
        if suppress is None:
            suppress = self._suppress
        self._add_log(str(text), 'info')
        self.echo(text, color='white')

    def error(self, text, suppress=None):
        """
        Add an error log
        """
        if suppress is None:
            suppress = self._suppress

        self._add_log(str(text), 'error')

        if not suppress:
            self.echo("ERROR: " + text, color='red')

    def warning(self, text, suppress=None):
        """
        Add a warning log
        """
        if suppress is None:
            suppress = self._suppress

        self._add_log(str(text), 'warning')

        if not suppress:
            self.echo("WARN: " + text, color='yellow')
    
    def exception(self, exception, suppress=None):
        """
        Add an exception log
        """
        if suppress is None:
            suppress = self._suppress
        if isinstance(exception, Exception):
            exceptionstr = traceback.format_exc(exception)
        else:
            exceptionstr = exception
        self._add_log(exceptionstr, 'exception')

        if not suppress:
            self.echo("EXCEPTION: " + exceptionstr, color='red')

    def warn(self, text, suppress=None):
        """
        Add a warning log
        """
        self.warning(text, suppress)

    def header(self, text, suppress=None):
        """
        Add a header log
        """
        if suppress is None:
            suppress = self._suppress

        subject = "======== {0} ========".format(text).upper()
        border = "="*len(subject)

        if not suppress:
            self.line()
            self.echo(border, color='white')
            self.echo(subject, color='white')
            self.echo(border, color='white')
            self.line()

        self._add_log(border, 'info')
        self._add_log(subject, 'info')
        self._add_log(border, 'info')

    def param(self, text, value, status, suppress=None):
        """
        Add a parameter/setting log
        """
        if suppress is None:
            suppress = self._suppress

        if value and not suppress:
            self.header("SETTING " + text)
            self.status(status)

    def configelement(self, name='', value='', separator=': ', suppress=None):
        """
        Add/display a configuration element
        """
        if suppress is None:
            suppress = self._suppress

        logoutput = '{0}{1}{2}'.format(str(name), str(separator), str(value))
        self.info(logoutput, suppress=True)
        if not suppress:
            click.secho(str(name), fg='cyan', bold=True, nl=False)
            click.secho(str(separator), fg='magenta', nl=False)
            click.secho(str(value), fg='white')

    def footer(self, text, suppress=None):
        """
        Add a footer log
        """
        if suppress is None:
            suppress = self._suppress
        self._add_log(str(text).upper(), 'info')
        if not suppress:
            self.info(text.upper())
            self.line()

    def procout(self, text, suppress=None):
        """
        Process output
        """
        if suppress is None:
            suppress = self._suppress
        if not suppress:
            self.echo(text, dim=True)

    def line(self, suppress=None):
        """
        Add a blank line
        """
        if suppress is None:
            suppress = self._suppress

        if not suppress:
            self.echo(text="")

    def echo(self, text, color="", dim=False):
        """
        Generic echo to screen (replaces print/pprint)
        """
        try:
            click.secho(text, fg=color, dim=dim)
        except:
            from pprint import pprint
            pprint(text)


OUTPUT = Output()
