
#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import

# Python 3 and compatibility with Python 2
import os
import emails
from jinja2 import Environment, FileSystemLoader

try:
    # Import as part of the aws_aware project
    from aws_aware.outputclass import OUTPUT
except ImportError:
    # Otherwise import locally and define out ouput stream manually
    from outputclass import Output as outstream
    OUTPUT = outstream()


class EmailNotification(object):
    """
    Email Notification Engine based on jinja templates
    """
    # Used to validate email addresses
    #EMAIL_REGEX = re.compile('([\w\-\.\']+@(\w[\w\-]+\.)+[\w\-]+)')

    # Used to determine if we are sending an html or text email
    #HTML_REGEX = re.compile('(^<!DOCTYPE HTML.*?>)')

    def __init__(self, smtphost, fromuser, fromemail, login=None,
                 password=None, ssl=True, port=25, templatedir='templates', verbose=False):

        # template extension
        self._template_extension = 'j2'
        self._smtphost = smtphost
        self._fromuser = fromuser
        self._fromemail = fromemail
        self._smtplogin = login
        self._smtppass = password
        self._ssl = ssl
        self._port = port
        self._verbose = verbose
        if os.path.isdir(templatedir):
            self._jinjatemplatedir = templatedir
        else:
            self._jinjatemplatedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates')

        self._env = Environment(loader=FileSystemLoader(self._jinjatemplatedir))

    def render_jinja_template(self, data, template):
        template = template + '.{0}'.format(self._template_extension)
        OUTPUT.info('Rendering template: {0}'.format(template))
        text = self._env.get_template(template)
        msg = text.render(data)
        return msg

    def send_email(self, html, subject, recipients, ccrecipients=None, attachments=None):
        """
        Send an email. recipients and ccrecipients is a list of 
        address-like elements, i.e.:
        * "name <email>"
        * "email"
        * (name, email)
        """
        message = emails.Message(
            html=html,
            subject=subject,
            mail_from=(self._fromuser, self._fromemail),
            mail_to=recipients,
            cc=ccrecipients)
        if attachments:
            for attachment in attachments:
                self._add_log('Attempting to attach file: {0}'.format(attachment))
                filename = os.path.split(attachment)[1]
                message.attach(filename=filename, data=open(attachment, 'rb'))

        if self._smtplogin:
            self._add_log('Attempting to use SMTP with authentication to: {0}:{1}'.format(self._smtphost, self._port))
            smtp = {'host': self._smtphost,
                    'port': self._port,
                    'ssl': self._ssl,
                    'user': self._smtplogin,
                    'password': self._smtppass}
        else:
            self._add_log('Attempting to use SMTP without authentication to: {0}:{1}'.format(self._smtphost, self._port))
            smtp = {'host': self._smtphost,
                    'port': self._port}

        save_html = os.getenv('AWS_AWARE_SAVE_EMAIL', False)

        if save_html:
            htmlfilepath = os.path.join( os.getcwd(), 'aws-instance-report.html')
            outputfile = open(htmlfilepath,"w")
            outputfile.write(html)
            outputfile.close()

        result = message.send(to=recipients, smtp=smtp)

        assert result.status_code == 250
        # if response.status_code not in [250, ]:
        # message is not sent, retry later

    def send_email_template(self, jinjatemplate, jinjadata, subject, recipients, ccrecipients=None, attachments=None):
        try:
            # Render our jinja template
            html = self.render_jinja_template(jinjadata, jinjatemplate)
        except Exception as jinjaexception:
            OUTPUT.error('Unable to render jinja template!')
            raise jinjaexception

        return self.send_email(
            html=html,
            subject=subject,
            recipients=recipients,
            ccrecipients=ccrecipients,
            attachments=attachments)

    def save_html_report(self, jinjatemplate, jinjadata, filename=None):
        """Save an html file instead of sending email"""
        try:
            # Render our jinja template
            html = self.render_jinja_template(jinjadata, jinjatemplate)
        except Exception as jinjaexception:
            OUTPUT.error('Unable to render jinja template!')
            raise jinjaexception

        if not filename:
            htmlfilepath = os.path.join( os.getcwd(), 'aws-instance-report.html')
        else:
            htmlfilepath = filename

        try:
            outputfile = open(htmlfilepath,"w")
            outputfile.write(html)
            outputfile.close()
        except Exception as smtplibraryexception:
            OUTPUT.error('Unable to save {0}!'.format(htmlfilepath))
            raise smtplibraryexception
    

    def _add_log(self, mylog, logtype='info'):
        """Add a log generated from this module"""
        if logtype == 'error':
            OUTPUT.error('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))
        elif logtype == 'warning':
            OUTPUT.warning('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))
        else:
            OUTPUT.info('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))


if __name__ == "__main__":
    from datetime import date
    # Example with on screen logging

    emailhandler = EmailNotification(
        smtphost='localhost',
        fromuser='ERM Notice',
        fromemail='ERMNotice@eventing',
        templatedir='../config/templates',
        verbose=True)

    # Jinja requires this entire data structure for the included
    # templates. recipients are automatically split by semicolon and sent to
    # individually.
    mydata = {
        "emailtitle": "EMR Job Status",
        "date": date.today().strftime('%d, %b %Y'),
        "data": {
            "Job Status": "Successful",
            "Something Else": "Another Value",
            "LastOperation": "Cancellation",
            "Cool Cats": "Bill, Charles, and Kaab"
        }
    }

    emailhandler.send_email_template(
        jinjatemplate='email-html_destructfailure',
        jinjadata=mydata,
        subject='EMR Destruct Failure',
        recipients=['consultant@mycompany.com'],
        ccrecipients=['zloeber@gmail.com'],
        attachments=['/home/tibco/ingestion/FoundationServices/PRL3_Cloud/EMR/lib/142301_towerlog.txt'])
