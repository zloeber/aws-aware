"""
Monitor base and sub-classes
"""
from __future__ import absolute_import
from datetime import date
import sys
import os
import yaml

# Allow for use outside of this module like a nice guy
try:
    from aws_aware.scriptconfig import CFG, RUNARGS, MONITORARGS, SCRIPTPATH, OUTPUT
    from aws_aware.compat import MutableMapping
    from aws_aware.awslibrary import mycompanyAWS
    from aws_aware.slack import SlackPoster
except:
    from outputclass import Output as outstream
    OUTPUT = outstream()
    from scriptconfig import CFG, RUNARGS, MONITORARGS, SCRIPTPATH
    from compat import MutableMapping
    from awslibrary import mycompanyAWS
    from slack import SlackPoster

# Allowed to be exported
__all__ = ['MonitorTasks', 'Monitor']

MONITOR_ATTRIBUTES = {
    'name': None,
    'thresholdtype': 'Instance',
    'warningthreshold': 0,
    'alertthreshold': 0,
    'enabled': False,
    'count': 0,
}

class Monitor(MutableMapping):
    """
    Monitor object that consists of data representing various AWS monitoring thresholds.

    Example: monitorjobs = Monitor()
    """

    def __init__(self, *args, **kwargs):
        """
        All Monitor specific attributes.
        """
        self.monitor_attributes = MONITOR_ATTRIBUTES.copy()

        # Initialize the data dictionary for the default settings
        allowedattribs = {}

        # Use passed in parameters only in our allowed list,
        # if not available then set them to default values.
        for key in self.monitor_attributes.iterkeys():
            lowerkey = str(key).lower()
            allowedattribs[lowerkey] = kwargs.pop(key, self.monitor_attributes[key])

        # update our base dict with all items
        self.__dict__.update(*args, **allowedattribs)

    # The next five methods are requirements of the ABC object.
    def __setitem__(self, key, value):
        # Only update items that are in our list of properties
        if key in self.monitor_attributes.iterkeys():
            self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        """No deletion of our keys please!"""
        #del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        '''returns simple dict representation of the mapping'''
        return str(self.__dict__)

    def __repr__(self):
        '''echoes class, id, & reproducible representation in the REPL'''
        return '{}, Monitor({})'.format(super(Monitor, self).__repr__(), self.__dict__)

    def _add_log(self, mylog, logtype='info'):
        """Add a log generated from this module"""
        if logtype == 'error':
            OUTPUT.error('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))
        elif logtype == 'warning':
            OUTPUT.warning('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))
        else:
            OUTPUT.info('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))

    def to_dict(self):
        """Returns a plain dict"""
        return self.__dict__

    def update(self, element, value):
        """Shortcut method to update a propery"""
        self._add_log('{1} -> {2}'.format(element, value))
        self.__setitem__(element, value)

    def show(self):
        """Prints information about current monitor to console"""
        return[(self.name), str(self.thresholdtype), str(self.warningthreshold), str(self.alertthreshold), str(self.enabled)]

    def load_from_file(self, filepath=None):
        """Return a list of Monitor object from a yaml file."""
        if filepath:
            self._add_log('Loading monitor configuration - {0}'.format(filepath))
            try:
                monitordata = yaml.load(open(filepath))
            except Exception as monitorclassexception:
                raise monitorclassexception

            monitorjobs = []

            for monitor in monitordata:
                self._add_log('Loading monitor: {0}'.format(monitor['name']))
                monitorjobs.append(
                    Monitor(
                        name=monitor['name'],
                        thresholdtype=monitor['thresholdtype'],
                        warningthreshold=monitor['warningthreshold'],
                        alertthreshold=monitor['alertthreshold'],
                        enabled=monitor['enabled']
                    )
                )

            return monitorjobs

    def show_monitors(self, monitors):
        """Prints information about a list of monitors to console"""
        try:
            OUTPUT.info('Loading and displaying monitors')

            outlines = []
            outlines.append(['name', 'thresholdtype', 'warn_thresh', 'alert_thresh', 'enabled'])
            for monitor in monitors:
                outlines.append(monitor.show())

            col_width = max(len(word) for row in outlines for word in row) + 2
            # padding
            for row in outlines:
                OUTPUT.echo("".join(word.ljust(col_width) for word in row))

        except Exception as monitorexception:
            OUTPUT.error('Unable to print monitor output')
            raise monitorexception


class MonitorTasks(object):
    """
    Run Monitor tasks.
    """

    def __init__(self, *args, **kwargs):
        self.monitorconfig = kwargs.pop('monitorconfig', os.path.join(SCRIPTPATH, ('config' + os.sep + 'default-monitor.yml')))
        self.monargs = kwargs.pop('monargs', MONITORARGS)
        self.runargs = kwargs.pop('runargs', RUNARGS)
        self.includeundefined = kwargs.pop('includeundefined', False)
        self.aws = None
        self.monitorjobs = []
        self.warningthresholdreached = False
        self.alertthresholdreached = False
        self.sendwarnings = False
        self.sendalerts = False
        self.allinstances = None
        self.instances = None
        self.skipprobe = False
        self.datapath = None
        self.view = None
        self.filters = None

        # Load monitor definitions
        try:
            self.load_monitor_config()
        except:
            raise Exception('Unable to open monitor definition: {0}'.format(self.monitorconfig))

        if self.monargs['skipprobe']:
            try:
                self.instances = self.load_instance_data(datapath=self.datapath)
            except:
                raise Exception('Unable to open data file ({0}). Perhaps a probe is required.'.format(self.datapath))

    def _add_log(self, mylog, logtype='info'):
        """Add a log generated from this module"""
        if logtype == 'error':
            OUTPUT.error('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))
        elif logtype == 'warning':
            OUTPUT.warning('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))
        else:
            OUTPUT.info('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))

    def eval_filter(self, argname):
        """Returns evaluated arg name"""
        result = '*'
        if self.monargs:
            if (self.monargs[argname]):
                result = str(self.runargs[argname])
        if self.filters:
            if (self.filters[argname]):
                result = str(self.filters[argname])
        return result

    def costcenter(self):
        """Returns evaluated cost center"""
        return self.eval_filter('costcenter')

    def appname(self):
        """Returns evaluated appname"""
        return self.eval_filter('appname')

    def environment(self):
        """Returns evaluated environment"""
        return self.eval_filter('environment')

    def filter_instance_by(self, key, val, instances):
        """Returns filtered list of instances based on key/value pairs"""
        return list(filter(lambda d, val=val: d[key] == val, instances))

    def load_monitor_config(self, monitorconfig=None):
        """Load a monitor configuration file into this collection"""
        if monitorconfig is None:
            monitorconfig = self.monitorconfig

        self._add_log('Loading monitor configuration - {0}'.format(monitorconfig))

        monitorconfig = yaml.load(open(monitorconfig))
        self.monitorjobs = [
            # Default catch all bucket
            Monitor(
                name='Other',
                thresholdtype='instance',
                warningthreshold=0,
                alertthreshold=0,
                enabled=self.includeundefined
            ),
        ]

        for monitor in monitorconfig['monitors']:
            self._add_log('Adding monitor: {0}'.format(monitor['name']))
            self.monitorjobs.append(
                Monitor(
                    name=monitor['name'],
                    thresholdtype=monitor['thresholdtype'],
                    warningthreshold=monitor['warningthreshold'],
                    alertthreshold=monitor['alertthreshold'],
                    enabled=monitor['enabled']
                )
            )

        self.view = monitorconfig['view']
        self.filters = monitorconfig['filters']

        if not self.view['column_lookup']:
            self.view['column_lookup'] = {
                'CostCenter': 'Cost Center',
                'ApplicationName': 'App Name',
                'Environment': 'Env',
                'ProcessName': 'Process Name',
                'Cloudera-Director-Template-Name': 'CDH Role',
                'aws:elasticmapreduce:instance-group-role': 'EMR Role',
                'launch_time': 'Launched',
                'public_ip_address': 'Public IP',
                'private_ip_address': 'Private IP',
                'cluster': 'Cluster',
                'instance_type': 'Instance Type',
                'name': 'Name',
            }
        
        if not self.view['notice_columns']:
            self.view['notice_columns'] = {'cluster', 'ApplicationName', 'ProcessName', 'instance_type'}

        # self.monitorjobs['verboseemailnotices'] = (True if str(self.runargs['verboseemailnotices']).lower() == 'true' else False)

    def load_instance_data(self, datapath=None):
        """Load a instance data from a file"""
        if not datapath:
            datapath = self.datapath

        self._add_log('Loading instance data - {0}'.format(datapath))
        instancedata = yaml.load(open(datapath))
        return instancedata

    def show_monitors(self):
        """Prints information about current monitors to console"""
        try:
            OUTPUT.info('Loading and displaying monitors')

            outlines = []
            outlines.append(['name', 'thresholdtype', 'warn_thresh', 'alert_thresh', 'enabled'])
            for monitor in self.monitorjobs:
                outlines.append(monitor.show())

            col_width = max(len(word) for row in outlines for word in row) + 2
            # padding
            for row in outlines:
                OUTPUT.echo("".join(word.ljust(col_width) for word in row))

        except Exception as monitorexception:
            OUTPUT.error('Unable to print monitor output')
            raise monitorexception

    def send_notice(self):
        """
        Send job status update notifications if required.
        """
        if self.should_send_alert() or self.should_send_warning() or self.runargs['force']:
            # Send email notification to passed argument recipients if defined,
            #  otherwise send to stored recipients.
            recipients = self.runargs['emailrecipients']

            if recipients:
                status = 'Normal'
                if self.warningthresholdreached:
                    status = 'Warning'
                if self.alertthresholdreached:
                    status = 'Alert'
                # Jinja requires this entire data structure for the included
                # templates. recipients are automatically split by semicolon and sent to
                # individually.

                emaildata = {
                    "emailtitle": "AWS Aware Status: {0}".format(status),
                    "date": date.today().strftime('%m/%d/%Y'),
                    "monitors": self.monitorjobs,
                    "costcenter": self.costcenter(),
                    "environment": self.environment(),
                    "appname": self.appname(),
                    "instances": self.get_instances(),
                    "allinstances": self.get_instances(filtered=True),
                    "view": self.view,
                    "additionalnotes": 'Please review these thresholds and take appropriate action to reduce instance counts down to the approved level. Below are all instances with tag filters matching your CostCenter, Environment, and Application Name (but grouped by Process Name). Attached is a report of all instances returned in this environment for further review.'
                }
                CFG.emailhandler.send_email_template(
                    jinjatemplate='email-html_instance_monitor',
                    jinjadata=emaildata,
                    subject="AWS Aware Status: {0}".format(status),
                    recipients=str(recipients).split(';')
                )
            else:
                OUTPUT.warning('There are no recipients passed or defined for this job. Exiting.')

    def send_notice_with_report(self):
        """
        Send job status update notifications if required.
        """
        if self.should_send_alert() or self.should_send_warning() or self.runargs['force']:
            # Send email notification to passed argument recipients if defined,
            #  otherwise send to stored recipients.
            recipients = self.runargs['emailrecipients']

            if recipients:
                status = 'Normal'
                if self.warningthresholdreached:
                    status = 'Warning'
                if self.alertthresholdreached:
                    status = 'Alert'
                # Jinja requires this entire data structure for the included
                # templates. recipients are automatically split by semicolon and sent to
                # individually.

                reportdata = {
                    "title": 'All Instances',
                    "date": date.today().strftime('%m/%d/%Y'),
                    "monitors": self.monitorjobs,
                    "costcenter": '*',
                    "environment": '*',
                    "appname": '*',
                    "instances": self.get_instances(),
                    "allinstances": self.get_instances(filtered=True),
                    "additionalnotes": 'Includes running instances only.'
                }
                CFG.emailhandler.save_html_report(
                    jinjatemplate='report-html_instance_details',
                    jinjadata=reportdata
                )

                emaildata = {
                    "emailtitle": "AWS Aware Status: {0}".format(status),
                    "date": date.today().strftime('%m/%d/%Y'),
                    "monitors": self.monitorjobs,
                    "costcenter": self.costcenter(),
                    "environment": self.environment(),
                    "appname": self.appname(),
                    "instances": self.get_instances(),
                    "view": self.view,
                    "additionalnotes": 'Please review these thresholds and take appropriate action to reduce instance counts to the approved level. (Save, then open the attached report for further instance details grouped by the ProcessName tag)'
                }
                CFG.emailhandler.send_email_template(
                    jinjatemplate='email-html_instance_monitor',
                    jinjadata=emaildata,
                    subject="AWS Aware Status: {0}".format(status),
                    recipients=str(recipients).split(';'),
                    attachments=['./aws-instance-report.html']
                )
            else:
                OUTPUT.warning('There are no recipients passed or defined for this job. Exiting.')

    def send_instance_report(self, filteredinstances=False):
        """
        Send instance report.
        """
        # Send email notification to passed argument recipients if defined,
        #  otherwise send to stored recipients.
        recipients = self.runargs['emailrecipients']
        instances = self.get_instances(filtered=filteredinstances)
        instancecounts = self.get_all_instance_counts(instances=instances)
        if recipients:
            status = 'Normal'
            if self.warningthresholdreached:
                status = 'Warning'
            if self.alertthresholdreached:
                status = 'Alert'
            # Get instance counts
            # Jinja requires this entire data structure for the included
            # templates. recipients are automatically split by semicolon and sent to
            # individually.
            reportdata = {
                "title": 'Instance Report - {0}'.format(status),
                "date": date.today().strftime('%m/%d/%Y'),
                "view": self.view,
                "monitors": self.monitorjobs,
                "costcenter": str(self.costcenter()),
                "environment": str(self.environment()),
                "appname": str(self.appname()),
                "instances": instances,
                "instancecounts": instancecounts,
                "additionalnotes": '(Includes running instances only.)'
            }

            CFG.emailhandler.save_html_report(
                jinjatemplate='report-html_instance_details',
                jinjadata=reportdata
            )

            emaildata = {
                "emailtitle": "AWS Instances: Status = {0}".format(status),
                "date": date.today().strftime('%m/%d/%Y'),
                "view": self.view,
                "monitors": self.monitorjobs,
                "costcenter": self.costcenter(),
                "environment": self.environment(),
                "appname": self.appname(),
                "instances": None,
                "additionalnotes": 'To view this report please save it locally then open in your browser. Only running instances are included. Clusters are sorted by name then instance type. Review all clusters to ensure they are aligned with your application requirements.'
            }

            emaildata['instances'] = self.get_instances(filtered=filteredinstances)
            emaildata['costcenter'] = str(self.costcenter()[0])
            emaildata['environment'] = str(self.environment()[0])
            emaildata['appname'] = str(self.appname()[0])

            CFG.emailhandler.send_email_template(
                jinjatemplate='email-html_instance_monitor',
                jinjadata=emaildata,
                subject="AWS Aware Instance Report",
                recipients=str(recipients).split(';'),
                attachments=['./aws-instance-report.html']
            )
        else:
            OUTPUT.warning('There are no recipients passed or defined for this job. Exiting.')

    def should_send_warning(self):
        """Should we send a warning?"""
        if self.sendwarnings and self.warningthresholdreached:
            return True
        else:
            return False

    def should_send_alert(self):
        """Should we send an alert?"""
        if self.sendalerts and self.alertthresholdreached:
            return True
        else:
            return False

    def get_slackmessage(self):
        """Returns a dictionary that can be used to send a slack notification via json webhook"""
        color = 'good'
        mes_type = 'Status'
        if self.warningthresholdreached:
            color = '#FFFF00'
            mes_type = 'Warning'
        if self.alertthresholdreached:
            color = 'danger'
            mes_type = 'Alert'
        else:
            color = '#FFA500'
            mes_type = 'Status'

        monitorinfo = [
            {
                "title": "Notice Level",
                "value": mes_type,
                "short": True
            }
        ]

        slacknotice = {
            "attachments": [
                {
                    "fallback": "AWS Instance Threshold Check ({0})".format(mes_type),
                    "text": "AWS Instance Threshold Check ({0})".format(mes_type),
                    "color": color,
                    "fields": monitorinfo
                }
            ]
        }
        return slacknotice

    def send_slack_notification(self, force=False):
        """Send a slack notification"""
        if force or self.should_send_warning() or self.should_send_alert():
            if CFG.values.has_key('slack_webhooks') and CFG.values.has_key('slack_notifications'):
                if CFG.values['slack_webhooks'] and CFG.values['slack_notifications']:
                    slk = SlackPoster(CFG.values['slack_webhooks'])
                    slackmessage = self.get_slackmessage()
                    if slackmessage:
                        slk.post_message(slackmessage)
                else:
                    OUTPUT.info('Slack notifications not enabled or there are no webhooks defined.')

    def instantiate_aws(self):
        """Connect to AWS"""
        # create a new connection with AWS
        try:
            self.aws = mycompanyAWS(awsid=self.runargs['awsid'], awssecret=self.runargs['awssecret'], profileid=self.runargs['awsprofile'], region=self.runargs['awsregion'])
        except:
            self.exit_with_exception('AWS Connection Failure')

    def awsinstancename_to_clustername(self, awsid=''):
        """ Convert aws ids into cluster names 
            awsid='team1-prod-stb-331-0dc72cb9-67ec-4bfc-9af9-a6e1aa50adfb'
            clustername='team1-prod-stb-331'
        """
        if awsid:
            awsidarr = awsid.split('-')
            if len(awsidarr) >= 5:
                return '-'.join(awsidarr[:5])
        else:
            return ''

    def poll_instance_data(self):
        """Poll AWS for data we need"""
        if self.skipprobe:
            # Pull prior aws information
            try:
                OUTPUT.info('Loading prior instance data: {0}'.format(self.datapath))
                self.allinstances = self.load_instance_data(datapath=self.datapath)
            except Exception as monitorclassexception:
                raise monitorclassexception
            
            self.instances = self.allinstances
            if self.environment() != '*':
                self.instances = [i for i in self.instances if i['Environment'] == self.environment()]
            if self.appname() != '*':
                self.instances = [i for i in self.instances if i['ApplicationName'] == self.appname()]
            if self.costcenter() != '*':
                self.instances = [i for i in self.instances if i['CostCenter'] == self.costcenter()]
        else:
            self._add_log('Polling AWS for instance data')
            # Get aws going
            try:
                OUTPUT.info('Instantiating connection to AWS first...')
                self.instantiate_aws()
            except Exception as monitorclassexception:
                raise monitorclassexception

            otherfilters = []

            # Other filter definitions
            # Running instances
            otherfilters.append({'Name': 'instance-state-name', 'Values': self.view['instance_state']})

            # Particular cost center
            tag_cc = str(self.costcenter())
            self._add_log('Other Filter - CostCenter: {0}'.format(tag_cc))
            otherfilters.append({'Name': 'tag:CostCenter', 'Values': [tag_cc]})

            # ApplicationName
            tag_app = str(self.appname())
            self._add_log('Other Filter - ApplicationName: {0}'.format(tag_app))
            otherfilters.append({'Name': 'tag:ApplicationName', 'Values': [tag_app]})

            # Environment
            tag_env = str(self.environment())
            self._add_log('Other Filter - Environment: {0}'.format(tag_env))
            otherfilters.append({'Name': 'tag:Environment', 'Values': [tag_env]})

            self._add_log('Instance filters applied: {0}'.format(len(otherfilters)))
            # Basic instance dictionary list result with some additional tags.
            self.allinstances = self.aws.aws_instances_brief(
                otherfilters=otherfilters, 
                tags=self.view['instance_tags'])
            self._add_log('AWS instances found: {0}'.format(
                len(self.allinstances)))

            if self.allinstances:
                self._add_log('Inferring clustername attributes...')
                for instance in self.allinstances:
                    instance['cluster'] = self.awsinstancename_to_clustername(instance['name'])
            else:
                self._add_log('Zero AWS Instances found!')

            self.save_instance_data(filepath=self.runargs['datapath'])

    def icount(self, seq, pred):
        """Used for summing data"""
        return sum(1 for v in seq if pred(v))
    
    def get_instances(self, filtered=False):
        """Return currently loaded instances"""
        results = []
        if self.allinstances:
            results = self.allinstances
        if filtered:
            if self.environment() != '*':
                results = [i for i in results if i['Environment'] == self.environment()]
            if self.appname() != '*':
                results = [i for i in results if i['ApplicationName'] == self.appname()]
            if self.costcenter() != '*':
                results = [i for i in results if i['CostCenter'] == self.costcenter()]
        
        return results

    def update_instance_counts(self):
        """Update instance counts"""
        for monitor in self.monitorjobs:
            if monitor['enabled']:
                if (monitor['name'] == 'Other'):
                    if self.includeundefined:
                        self._add_log('Getting undefined instance types')
                        unknowns=self.get_unknown_instances()
                    else:
                        self._add_log('Skipping undefined instance types')
                        unknowns=0
                    monitor['count'] = unknowns
                
                self._add_log('Getting count for instance type: {0}'.format(monitor['name']))
                
                if self.instances:
                    newcount = self.icount(self.instances, lambda i, monitorname=monitor['name']: i['instance_type'] == monitorname)
                else:
                    self._add_log('  no instances to filter!')
                    newcount=0

                monitor['count'] = newcount
    
    def get_all_instance_counts(self, instances=None,  attribute='instance_type'):
        """Retrieve a count of all instances based on the passed attribute"""
        typecounts = {}
        if not instances:
            instances=self.get_instances()
        foundtypes = self.get_all_inst_attrib(instances=instances, attribute=attribute)

        for ftype in foundtypes:
            typecounts[ftype] = self.icount(instances, lambda i, attrib=attribute, val=ftype: i[attrib] == val)
            self._add_log('Count for attribute {0} found: {1}'.format(ftype, typecounts[ftype]))

        return typecounts

    def get_unknown_instancetypes(self):
        """Returns a list of unknown instance types"""
        unknowns = {}
        knowns = self.get_known_instancetypes()
        for instance in self.instances:
            iname = str(instance['instance_type'])
            if (iname not in knowns) and (iname != 'other'):
                if not unknowns.has_key(iname):
                    unknowns[iname] = False
        return unknowns.keys()

    def get_unknown_instances(self):
        """Returns a unknown instances"""
        unknowns = []
        if self.instances:
            knowntypes = self.get_known_instancetypes()
            for instance in self.instances:
                if str(instance['instance_type']) not in knowntypes:
                    unknowns.append([instance])
        
        return unknowns

    def get_all_inst_attrib(self, instances=None, attribute='instance_type'):
        """Returns a list of instance types for all collected instance data"""
        found_attribs = {}
        if not instances:
            instances=self.get_instances()

        for thisinst in instances:
            if thisinst.has_key(attribute):
                if not found_attribs.has_key(str(thisinst[attribute])):
                    found_attribs[str(thisinst[attribute])] = False

        return found_attribs.keys()

    def get_known_instancetypes(self):
        """Returns a list of known instance types"""
        knowns = {}
        for monitor in self.monitorjobs:
            if str(monitor['name']).lower() != 'Other':
                if (str(monitor['thresholdtype']).lower() == 'instance') and (not knowns.has_key(str(monitor['name']))):
                    knowns[str(monitor['name'])] = False
        return knowns.keys()

    def check_threshold_triggers(self):
        """Check if any thresholds have been reached"""
        for monitor in self.monitorjobs:
            if monitor['enabled']:
                if str(monitor['warningthreshold']) != '0':
                    if monitor['count'] >= monitor['warningthreshold']:
                        self.warningthresholdreached = True
                if str(monitor['alertthreshold']) != '0':
                    if monitor['count'] > monitor['alertthreshold']:
                        self.alertthresholdreached = True

    def save_instance_data(self, filepath=None):
        """Save instance data to disk"""
        if filepath is None:
            filepath = os.path.join(os.getcwd(), 'instance-output.yml')
        self._add_log('Saving instance data to: {0}'.format(filepath))
        yaml.dump(self.allinstances, file(filepath, 'wb'), encoding='utf-8', allow_unicode=True, default_flow_style=False)

    def save_html_report(self, 
        filteredinstances=False, reportname='instance_details.html'):
        """
        Save instance data to an html report
        """
        instances = self.get_instances(filtered=filteredinstances)
        instancecounts = self.get_all_instance_counts(instances=instances)
        status = 'Normal'
        if self.warningthresholdreached:
            status = 'Warning'
        if self.alertthresholdreached:
            status = 'Alert'
        # Jinja requires this entire data structure for the included
        # templates. recipients are automatically split by semicolon and sent to
        # individually.
        reportdata = {
            "title": "AWS Aware Status - {0}".format(status),
            "date": date.today().strftime('%m/%d/%Y'),
            "monitors": self.monitorjobs,
            "costcenter": self.costcenter(),
            "environment": self.environment(),
            "appname": self.appname(),
            "instances": instances,
            "instancecounts": instancecounts,
            "view": self.view,
            "additionalnotes": '(Running instances only.)'
        }
        CFG.emailhandler.save_html_report(
            jinjatemplate='report-html_instance_details',
            jinjadata=reportdata,
            filename=reportname
        )

    def exit_with_exception(self, cause='General Failure'):
        """
        This will result in exiting the application and cause tasks to
        return with failure status.

        PARAMETER: cause
        """

        OUTPUT.error('Exiting with exception cause: {0}'.format(str(cause)))
        sys.exit(1)

    def exit_without_exception(self):
        """
        Exit successfully.
        """
        sys.exit(0)
