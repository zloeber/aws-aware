"""
A few wrapper methods to make working with AWS boto3 library easier.
"""
from __future__ import absolute_import
import time
import string
import random
import re
import boto3
from botocore.exceptions import ClientError

try:
    # Import as part of the aws_aware project
    from aws_aware.outputclass import OUTPUT
except ImportError:
    # Otherwise import locally and define out ouput stream manually
    from outputclass import Output as outstream
    OUTPUT = outstream()


class AWSAPI(object):
    """AWSAPI wrapper library for boto3 based operations
        Author: Zachary Loeber
        About: A few wrapper methods to make working with AWS boto3 library easier.
    """

    def __init__(self, awsid=None, awssecret=None, profileid=None, region='us-east-1'):
        # AWS authentication information
        self.awsid = awsid
        self.secret = awssecret
        self.profileid = profileid
        self.region = region
        self.session = None
        self.ec2resource = None
        self.ec2 = None
        # Used in our subnet search functions (thanks to Bill!)
        self._foundsubnet = None
        self._desiredsubnetcount = 1

        # Setup a general connection
        self.connect_session()

        # try to connect session to ec2 resource instance
        self.connect_ec2()

    def _add_log(self, mylog, logtype='info'):
        """Add a log generated from this module"""
        if logtype == 'error':
            OUTPUT.error('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))
        elif logtype == 'warning':
            OUTPUT.warning('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))
        else:
            OUTPUT.info('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))

    def connect_session(self):
        """Connect with current profile or id/secret"""
        try:
            if self.profileid:
                OUTPUT.info('Using passed in profile - {0}'.format(self.profileid))
                self.session = boto3.Session(
                    profile_name=self.profileid,
                    region_name=self.region
                )
            else:
                self._add_log('Connecting to AWS with key id - {0}'.format(self.awsid))
                self.session = boto3.Session(
                    aws_access_key_id=self.awsid,
                    aws_secret_access_key=self.secret,
                    region_name=self.region
                )
        except ClientError as e:
            self._add_log(e, 'error')
            raise e

    def connect_ec2(self):
        """Attempt to connect session to ec2 resources"""
        self._add_log('Connecting to AWS ec2 resources with existing session.')
        try:
            self.ec2resource = self.session.resource('ec2')
            self.ec2 = self.session.client('ec2')
        except ClientError as e:
            self._add_log(e, 'error')
            raise e

    def getbotoclientconnection(self):
        # Returns the ec2 connection for direct use
        return self.ec2

    def getbotoresourceconnection(self):
        # Returns the ec2 connection for direct use
        return self.ec2resource

    def getavailablesubnet(self, desiredsubnetcount, subnetstosearch):
        self._desiredsubnetcount = int(desiredsubnetcount)
        subnets = subnetstosearch.split(',')

        self._add_log("Desired subnet count: {0}".format(self._desiredsubnetcount))

        for subnet in subnets:
            self._add_log("Searching subnet - {0}".format(subnet))
            lookup = self._show_subnet_usage(subnet)
            if lookup == 'found':
                return self._foundsubnet

    def _show_subnet_usage(self, query):
        # Really the main section it calls all the sub functions
        #  and all is passed back into this
        subnet = self._find_subnet(query)
        actual = int(subnet['AvailableIpAddressCount'])
        self._add_log("Actual subnets in {0}: {1}".format(subnet['SubnetId'], actual))

        if self._desiredsubnetcount < actual:
            self._add_log("Desired subnets = {0}, available subnets = {1}".format(self._desiredsubnetcount, actual))

            self._foundsubnet = subnet['SubnetId']
            return('found')

    def _find_subnet(self, query):
        # Finds the subnet based on subnet id
        #"""find a subnet by query (subnet ID or CIDR block)"""
        if re.match(r'^subnet-[a-fA-F0-9]+$', query):
            subnet = self._find_subnet_by_id(query)
        else:
            self._add_log("ERROR: {0} does not look like a subnet ID or CIDR block".format(query))

        return subnet

    def _find_subnet_by_id(self, subnet_id):
        # Formats the subnetid into a kwarg
        #"""find a subnet by subnet ID"""
        kwargs = {
            'SubnetIds': [subnet_id]
        }
        return self._find_classic_subnet(kwargs)

    def _find_classic_subnet(self, kwargs):
        # Searches AWS for the subnet infomration
        #"""call describe_subnets passing kwargs"""
        try:
            subnets = self.ec2.describe_subnets(**kwargs)['Subnets']
        except ClientError:
            return ''
        return subnets[0]

    def aws_instances(self, namefilter='*', otherfilters=None, asEC2resource=False):
        filters = [{'Name': 'tag:Name',
                    'Values': [namefilter + '*']}]
        if otherfilters:
            filters = filters + otherfilters

        self._add_log('aws_instances filters: {0}'.format(str(filters)))
        results = []

        reservations = self.ec2.describe_instances(Filters=filters)

        for r in reservations.get('Reservations'):
            for i in r['Instances']:
                if asEC2resource:
                    res = boto3.resource('ec2')
                    thisinstance = res.Instance(i['InstanceId'])
                    results.append(thisinstance)
                else:
                    results.append(i)

        return results
        # return reservations.get('Reservations')

    def aws_instances_brief(self, namefilter='*', otherfilters=None, attributes=['instance_type', 'private_ip_address', 'public_ip_address', 'launch_time'], tags=[]):
        """
        Same as aws_instances but at a much higher level 
        (using just boto3.resource instead of boto3.client)
        """
        filters = [{'Name': 'tag:Name',
                    'Values': [namefilter + '*']}]

        # Add any additional filters
        if otherfilters:
            filters = filters + otherfilters

        # Log our filter used
        self._add_log('aws_instances_brief filters: {0}'.format(str(filters)))

        # Get all instances matching our filters
        instances = self.ec2resource.instances.filter(Filters=filters)

        results = []
        taginfo = {}
        # Create a base dictionary of empty tags
        for tag in tags:
            if isinstance(tag, str):
                taginfo[tag] = None
            elif isinstance(tag, list):
                # If we have a list then only the first on matters
                taginfo[tag[0]] = None

        # Loop through all instances and pull any info
        for instance in instances:
            name = None
            inst = {
                'id': instance.id,
                'name': name,
                'state': instance.state['Name']
            }

            # Loop through tags for info
            for tag in instance.tags:
                # always grab the name
                if tag['Key'] == 'Name':
                    inst['name'] = tag['Value']

                # then grab any other defined tags we want
                if tag['Key'] in tags:
                    taginfo[tag['Key']] = tag['Value']

            # Update any attributes found
            for attr in attributes:
                inst[attr] = getattr(instance, attr)

            # Add any found tags to the instance results
            inst.update(taginfo)

            # Add final instance info to our results list
            results.append(inst)

        return results

    def aws_instance_by_private_ip(self, ipaddress):
        filters = [{
            'Name': 'private-ip-address',
            'Values': [ipaddress]
        }]
        result = self.aws_instances(otherfilters=filters)
        return result

    def aws_node_count(self, namefilter='*'):
        """Report nodes found in AWS"""
        self._add_log("Looking for nodes matching: {0}".format(namefilter))
        nodes = self.aws_instances(namefilter=namefilter)
        return len(nodes)

    def s3_folder_exists(self, bucket, folderpath):
        """Check for s3 folder"""
        self._add_log("Validating if {0} exists in {1}".format(folderpath, bucket))
        s3 = self.session.client('s3')
        result = s3.list_objects(Bucket=bucket, Prefix=folderpath)
        exists = False
        if result:
            exists = True
        return exists

    def s3_file_exists(self, bucket, filepath):
        """Check for s3 file"""
        self._add_log("Validating if {0} exists in {1}".format(filepath, bucket))
        s3 = self.session.client('s3')
        result = s3.list_objects(Bucket=bucket, Prefix=filepath)
        exists = False
        if result:
            exists = True
        return exists

    def download_s3_file(self, bucket, path, destpath):
        s3resource = self.session.resource('s3')
        self._add_log('downloading file: bucket - {0} ; file - {1}; desination - {2}'.format(bucket, path, destpath))
        try:
            download = s3resource.Bucket(bucket).download_file(path, destpath)
            return True
        except:
            return False

    def execute_commands_on_instances(self, commands, instance_ids, os='linux'):
        """Runs commands on remote linux instances
        :param client: a boto/boto3 ssm client
        :param commands: a list of strings, each one a command to execute on the instances
        :param instance_ids: a list of instance_id strings, of the instances on which to execute the command
        :return: the response from the send_command function (check the boto3 docs for ssm client.send_command() )
        """
        if str(os).lower() == 'windows':
            documentname = 'AWS-RunPowerShellScript'
        else:
            documentname = 'AWS-RunShellScript'
        ssm = self.session.client('ssm')
        resp = ssm.send_command(
            DocumentName=documentname,  # One of AWS' preconfigured documents
            Parameters={'commands': commands},
            InstanceIds=instance_ids
        )
        return resp

    def get_arn_from_key(self, key):
        iam = self.session.client('iam')

        try:
            key_info = iam.get_access_key_last_used(AccessKeyId=key)
            return key_info['UserName']
        except ClientError as e:
            self._add_log('Received error: {0}'.format(e), 'error')
            if e.response['Error']['Code'] == 'AccessDenied':
                return "Key does not exist in target account or you are not allowed to access it"


class mycompanyAWS(AWSAPI):
    """A set of mycompany specific AWS methods. Can be initialized as follows:
      aws = mycompanyAWS(awsid='awsid', awssecret='awssecret')

    Can also use a local cached profile:
      aws = mycompanyAWS(profile='profilename')

    default region is us-east-1 but can be passed in upon initalization with the region parameter:
      aws = mycompanyAWS(awsid='awsid', awssecret='awssecret', region='us-east-1')

    Can also include verbose console output for troubleshooting:
      aws = mycompanyAWS(awsid='awsid', awssecret='awssecret', verbose=True)
    """

    def __init__(self, *args, **kwargs):
        # pass through all args to the base class init
        super(mycompanyAWS, self).__init__(*args, **kwargs)

    def cloudera_cdh_gateway_ips(self, namefilter='*'):
        # Note: this only returns the first interface result of the first
        #  instance found with the filter!
        gwfilter = [{'Name': 'tag:Cloudera-Director-Template-Name',
                     'Values': ['gateways']}]

        reservations = self.aws_instances(namefilter=namefilter, otherfilters=gwfilter)
        results = []

        for reservation in reservations:
            for instance in reservation['Instances']:
                for interface in instance['NetworkInterfaces']:
                    results.append(interface['PrivateIpAddress'])

        return results

    def cloudera_emr_gateway_ips(self, namefilter='*'):
        # Note: this only returns the first interface result of the first
        #  instance found with the filter!
        gwfilter = [{'Name': 'tag:aws:elasticmapreduce:instance-group-role',
                     'Values': ['MASTER']}]

        instances = self.aws_instances(namefilter=namefilter, otherfilters=gwfilter)
        results = []

        # for reservation in reservations:
        for instance in instances:
            for interface in instance['NetworkInterfaces']:
                results.append(interface['PrivateIpAddress'])

        return results

    def get_emr_response_filename(self,
                                  cluster,
                                  bucketrootfolder='path'):
        if cluster and bucketrootfolder:
            return "{0}/{1}/emr-response.json".format(
                bucketrootfolder,
                cluster)

    def get_emr_fabfile_name(self,
                             bucketrootfolder='application',
                             fabfilename='fabfile.py'):
        """We take the cluster name and strip off the unique id
        to get the base cluster build location. This assumes
        that the cluster names are in the following format:
        'team2s-subteam-uat-##'
        """
        #if cluster:
        #    clustertemplate = '-'.join(cluster.split('-')[0:4])
        if bucketrootfolder:
            return "{0}/{1}".format(
                bucketrootfolder,
                fabfilename)

    def get_emr_paramfile_name(self,
                               cluster='',
                               bucketrootfolder='application',
                               paramfilename='defaultparams.yml'):
        """We take the cluster name and strip off the unique id
        to get the base cluster build location. This assumes
        that the cluster names are in the following format:
        'team2s-subteam-uat-##'
        """
        if cluster:
            clustertemplate = '-'.join(cluster.split('-')[0:4])
        if cluster and bucketrootfolder:
            return "{0}/{1}/{2}".format(
                bucketrootfolder,
                clustertemplate,
                paramfilename)

    def get_cdh_response_filename(self, cluster, bucketrootfolder='path'):
        return "{0}/{1}/response.yml".format(
            bucketrootfolder,
            cluster)

    def get_emr_response_content(self, bucket, cluster, bucketrootfolder='path'):
        filename = self.get_emr_response_filename(cluster, bucketrootfolder)
        s3 = self.session.client('s3')
        self._add_log('downloading data: bucket - {0} ; file - {1}'.format(bucket, filename))
        data = s3.get_object(Bucket=bucket, Key=filename)
        return data

    def get_cdh_response_content(self, bucket, cluster, bucketrootfolder='path'):
        filename = self.get_cdh_response_filename(cluster, bucketrootfolder)
        s3 = self.session.client('s3')
        self._add_log('downloading data: bucket - {0} ; file - {1}'.format(bucket, filename))
        data = s3.get_object(Bucket=bucket, Key=filename)
        return data

    def download_emr_response_file(self, bucket, bucketrootfolder, cluster, destpath):
        filename = self.get_emr_response_filename(cluster, bucketrootfolder)
        self.download_s3_file(bucket, filename, destpath)

    def download_emr_fabfile(self, bucket, bucketrootfolder, destpath, fabfile='fabfile.py', skipchecks=False):
        fabfilename = self.get_emr_fabfile_name(
            bucketrootfolder=bucketrootfolder,
            fabfilename=fabfile)
        if not skipchecks:
            if self.s3_file_exists(bucket, fabfilename):
                return self.download_s3_file(bucket, fabfilename, destpath)
        else:
            return self.download_s3_file(bucket, fabfilename, destpath)

    def download_emr_defaultparamfile(self, bucket, bucketrootfolder, destpath, paramfile='defaultparams.yml', skipchecks=False):
        """Download an emr default parameter file from S3"""
        paramfilename = "{0}/{1}".format(bucketrootfolder, paramfile)

        if not skipchecks:
            if self.s3_file_exists(bucket, paramfilename):
                return self.download_s3_file(bucket, paramfilename, destpath)
        else:
            return self.download_s3_file(bucket, paramfilename, destpath)

    def random_generator(self, size=6, chars=None):
        if not chars:
            chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
        self._add_log('Generating random string of {0} characters'.format(size))
        return ''.join(random.choice(chars) for x in range(size))

    def get_cluster_uniqueid(self, clusterbase='', maxlen=28, maxretry=10, waittime=10):
        if len(clusterbase) >= maxlen:
            raise Exception('Cluster base name length ({0}) is already equal or greater than the maximum length defined ({1})'.format(len(clusterbase), maxlen))
        if not clusterbase:
            raise Exception('Cluster base cannot be an empty string.')
        # Determine if we have been sent a cluster base with a hyphen divider or not
        if (clusterbase[len(clusterbase)-1:]) == '-':
            raise Exception('Cluster base name has been passed with a hyphen a the end')

        uniqueidlen = maxlen - len(clusterbase) - 1

        if uniqueidlen <= 0:
            raise Exception('Unique ID is not able to be generated as all characters have already been used up in the base cluster name (plus an additional hyphen divider)')

        retries = 0
        while retries < maxretry:
            retries = retries + 1
            self._add_log('Unique ID generation attempt {0} of {1}'.format(retries, maxretry))
            uniqueid = self.random_generator(size=uniqueidlen)
            clustername = '{0}-{1}'.format(clusterbase, uniqueid)
            self._add_log('Generated unique ID of {0}. Looking for any other instances that may already be using it.'.format(uniqueid))
            existingcount = self.aws_node_count(clustername)
            if existingcount == 0:
                return uniqueid
            self._add_log('Found {0} aws instances with the uniqueid of {1}, waiting for {2} seconds then trying again'.format(existingcount, clustername, waittime))
            time.sleep(waittime)


if __name__ == "__main__":
    """
    # Some good filters:
    # Running instances
    #filter_running = { 'Name': 'instance-state-name', 'Values': ['running']}
    # Particular cost center
    #filter_costcenter = { 'Name': 'tag:CostCenter', 'Values': ['0123456789']}
    # ApplicationName
    #filter_appname = { 'Name': 'tag:ApplicationName', 'Values': ['team1']}

    # Connect to AWS via local profile and verbose output (to screen)
    #aws = AWSAPI(awsprofile='tam', verbose=True)

    aws = mycompanyAWS(awsprofile='tam', verbose=True)

    # Conncet to AWS via id and secret with verbose logging (to screen)
    aws = AWSAPI(awsid='<someid>',
            awssecret='<somesecret>')

    a = aws.aws_instances('team2-dev-ufd-zKw')
    test = aws.aws_instance_by_private_ip('10.237.191.50')

    # Get the gateway IP of the master node for an EMR cluster
    gwip = aws.cloudera_emr_gateway_ips('team2-dev-subteam-38')

    test = aws.aws_instances('team2-dev-subteam-38')

    # This is almost guaranteed to loop through all the subnet lists and return no results
    result = aws.getavailablesubnet(1800,subnetlist)

    pprint(aws.aws_node_count('team1'))

    # Basic instance dictionary list result with some additional tags.
    report = aws.aws_instances_brief(namefilter='team1', otherfilters=[filter_running,filter_costcenter, filter_appname],tags=['CostCenter','ApplicationName'])

    pprint(report)

    # Same as above but with all the gritty details
    report2 = aws.aws_instances(namefilter='team2-dev-subteam-Na')
    # , otherfilters=[filter_running,filter_costcenter, filter_appname])

    # Sorted results by instance_type then name
    sortedreport = aws.multikeysort(report, ['instance_type','name'])

    # Filter just r3.4xlarge instances from our basic report
    r34xlarge = list(filter(lambda d: d['instance_type'] in ['r3.4xlarge'], report))

    pprint(r34xlarge)

    test = aws.aws_instance_by_ip('10.237.185.99')

    # download an emr-response.json file from a cluster deployment
    dl = aws.download_emr_response_file('useast1-team3-hadoop-dev','path','team2-dev-subteam-Lk',emrfile)
    with open(emrfile) as data_file:
        emrclusterdata = json.load(data_file)

    # Example of running a command against a linux instance
    #  (req. AmazonEC2RoleForSSM IAM role)
    commands = ['echo "hello world"']
    instance_ids = [str(emrclusterdata['clusterid'])]
    myresp = aws.execute_commands_instances(commands, instance_ids)

    # get a cdh response.yml content file and store in test
    test = aws.get_cdh_response_content('useast1-team3-hadoop-dev','team1-uat-stb-3644')

    # get an emr emr-response.json content file and store in test
    test2 = aws.get_emr_response_content('useast1-team3-hadoop-dev',' team2-dev-subteam-38')

    # Download emr fabfile
    downloadedfabfile = aws.download_emr_fabfile(
        bucket='useast1-team3-hadoop-dev',
        bucketrootfolder='application',
        cluster='team2-dev-subteam-x2',
        destpath='fabfile-subteam.py',
        fabfile='fabfile-subteam.py',
        skipchecks=True)

    subnetlist = 'subnet-1,subnet-2,subnet-3,subnet-4'
    """