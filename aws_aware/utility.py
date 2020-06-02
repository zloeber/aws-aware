"""
Utility function library for various tasks.
"""
from __future__ import absolute_import

from datetime import datetime
from operator import itemgetter
from collections import defaultdict, OrderedDict

import fnmatch
import os
import subprocess
import sys
import string
import random
import tarfile
import shutil
import re
import time
import json
import yaml
import requests

try:
    # Import as part of the aws_aware project
    from aws_aware.outputclass import OUTPUT
except:
    # Otherwise import locally and define out ouput stream manually
    from outputclass import Output as outstream
    OUTPUT = outstream()


class Utility(object):
    """
    Class of useful utility functions
    """

    def __init__(self):
        self._start = datetime.now()
        self.re_numeric_other = re.compile(r'(?:([0-9]+)|([-A-Z_a-z]+)|([^-0-9A-Z_a-z]+))')

        self.instance_sizes = [
            'micro',
            'small',
            'medium',
            'large',
            'xlarge',
            'x-large',
            'extra-large'
        ]
        self.pricing_urls = [
            # Deprecated instances (JSON format)
            'https://aws.amazon.com/ec2/pricing/json/linux-od.json',
            # Previous generation instances (JavaScript file)
            'https://a0.awsstatic.com/pricing/1/ec2/previous-generation/linux-od.min.js',
            # New generation instances (JavaScript file)
            'https://a0.awsstatic.com/pricing/1/ec2/linux-od.min.js'
        ]

    def _add_log(self, mylog, logtype='info'):
        """Add a log generated from this module"""
        if logtype == 'error':
            OUTPUT.error('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))
        elif logtype == 'warning':
            OUTPUT.warning('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))
        else:
            OUTPUT.info('{0}: {1}'.format(str(self.__class__.__name__), str(mylog)))

    def exe_proc(self, params, shell=False):
        """
        Execute a process
        """
        proc = subprocess.Popen(
            params, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=shell)

        stdout_data, stderr_data = proc.communicate()
        if stdout_data != "":
            OUTPUT.procout(self.decode(stdout_data))

        if proc.returncode != 0:
            self._add_log(self.decode(stderr_data), logtype='error')
            sys.exit()

    def call_proc(self, params, shell=False):
        """
        Call a process
        """
        try:
            subprocess.check_call(params, shell=shell)
        except KeyboardInterrupt as ki:
            return
        except Exception as e:
            self._add_log("Error while executing command: {0}. {1}".format(' '.join(params), str(e)), logtype='error')

    def is_dir_empty(self, name):
        """
        Check for empty directory
        """
        if os.path.exists(name):
            return len(os.listdir(name)) == 0
        else:
            return True

    def find_files(self, directory, pattern):
        """
        Find a file
        """
        # find all files in directory that match the pattern.
        for root, dirs, files in os.walk(directory):
            for basename in files:
                if fnmatch.fnmatch(basename, pattern):
                    filename = os.path.join(root, basename)
                    yield filename

    def get_file_contents(self, file):
        """
        Open a file and return its contents
        """
        with open(file, "r") as file:
            return file.read()

    def decode(self, val):
        """
        decode a value
        """
        return val.decode("utf-8").strip()

    def which(self, file_name):
        '''
        which command equivalent in python
        '''
        for path in os.environ["PATH"].split(os.pathsep):
            full_path = os.path.join(path, file_name)
            if os.path.exists(full_path) and os.access(full_path, os.X_OK):
                return full_path
        return None

    def get_timer(self):
        '''
        returns the time elapsed since this class was created
        '''
        return str(datetime.now() - self._start)

    def reset_timer(self):
        '''
        restarts the timer
        '''
        self._start = datetime.now()

    def make_tarfile(self, outfile, sourcepath, tarpath=None):
        """
        Create a tar.gz file from a path
        """
        if tarpath is None:
            tarpath = os.path.split(sourcepath)[1]
        with tarfile.open(outfile, "w:gz") as tar:
            tar.add(sourcepath, arcname=tarpath)

    def append_binary_to_text_file(self, textfile, binaryfile, outfile):
        """
        Append binary to a text file
        """
        # First copy the original to the new file
        shutil.copy(textfile, outfile)
        block_size = 1024 * 1024
        if hasattr(os, 'O_BINARY'):
            o_binary = getattr(os, 'O_BINARY')
        else:
            o_binary = 0

        # Then append the binary to the new file
        input_file = os.open(binaryfile, os.O_RDONLY | o_binary)
        with open(outfile, "ab") as fl:
            while True:
                input_block = os.read(input_file, block_size)
                if not input_block:
                    break
                fl.write(input_block)
        fl.close()

    def dos2unix(self, filename):
        """
        dos2unix in python
        """
        try:
            original_lines = open(filename).readlines()
        except UnicodeDecodeError:
            self._add_log("dos2unix: ignoring {0} because it is a binary file".format(filename))
            return
        new_lines = []
        for original_line in original_lines:
            for new_line in original_line.splitlines(False):
                new_line += '\n'
                new_lines.append(new_line)
        if original_lines == new_lines:
            return
        self._add_log("dos2unix: Converting lines in {0}".format(filename))
        open(filename, "w+").writelines(new_lines)

    def random_generator(self, size=6, chars=None):
        """
        generate random strings
        """
        if not chars:
            chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
        self._add_log('Generating random string of {0} characters'.format(size))
        return ''.join(random.choice(chars) for x in range(size))

    def get_pythonpath(self):
        """
        Return the path of the current python interpreter
        """
        return sys.executable

    def get_param_file_property(self, filepath, propertyname):
        """
        Retrieves the property value of a yaml parameter file
        """
        self._add_log('get_param_file_property: Attempting to retrieve {0} from {1}'.format(propertyname, filepath))
        yamlfile = yaml.safe_load(file(filepath, 'r'))
        if propertyname in yamlfile.keys():
            return yamlfile[propertyname]

    def update_param_file(self, filepath, element, value):
        """
        Update a yaml file with a new element value
        """
        self._add_log('Attempting to update {0} - {1} -> {2}'.format(filepath, element, value))
        yamldata = yaml.safe_load(file(filepath, 'r'))

        yamldata[element] = value

        yaml.safe_dump(yamldata, file(filepath, 'w'), encoding='utf-8', allow_unicode=True, default_flow_style=False)

    def multikeysort(self, items, columns):
        """Sorts lists of dictionaries based on keys"""

        comparers = [((itemgetter(col[1:].strip()), -1) if col.startswith('-') else (itemgetter(col.strip()), 1)) for col in columns]

        def comparer(left, right):
            for fn, mult in comparers:
                result = cmp(fn(left), fn(right))
                if result:
                    return mult * result
            else:
                return 0
        return sorted(items, cmp=comparer)

    def sort_nested_dict(self, value):
        """
        Recursively sort a nested dict.
        """
        result = OrderedDict()

        for key, val in sorted(value.items(), key=self.sort_ec2_key_by_numeric_other):
            if isinstance(val, (dict, OrderedDict)):
                result[key] = self.sort_nested_dict(val)
            else:
                result[key] = val

        return result

    def sort_ec2_key_by_numeric_other(self, key_value):
        """
        Split key into numeric, alpha and other part and sort accordingly.
        """
        return tuple((
            int(numeric) if numeric else None,
            self.instance_sizes.index(alpha) if alpha in self.instance_sizes else alpha,
            other
        ) for (numeric, alpha, other) in self.re_numeric_other.findall(key_value[0]))

    def scrape_ec2_pricing(self):
        """
        Scrapes web to create a json data file containing all known
        current AWS ec2 instance types and costs. Works in conjunction with
        update_ec2_pricing_file
        """
        import demjson
        result = {}
        result['regions'] = []
        result['prices'] = defaultdict(OrderedDict)
        result['models'] = defaultdict(OrderedDict)

        for url in self.pricing_urls:
            response = requests.get(url)

            if re.match('.*?\.json$', url):
                data = response.json()
            elif re.match('.*?\.js$', url):
                data = response.content
                match = re.match('^.*callback\((.*?)\);?$', data, re.MULTILINE | re.DOTALL)
                data = match.group(1)
                # demjson supports non-strict mode and can parse unquoted objects
                data = demjson.decode(data)

            regions = data['config']['regions']

            for region_data in regions:

                region_name = region_data['region']

                if region_name not in result['regions']:
                    result['regions'].append(region_name)

                libcloud_region_name = region_name
                instance_types = region_data['instanceTypes']

                for instance_type in instance_types:
                    sizes = instance_type['sizes']
                    for size in sizes:

                        price = size['valueColumns'][0]['prices']['USD']
                        if str(price).lower() == 'n/a':
                            # Price not available
                            continue

                        if not result['models'][libcloud_region_name].has_key(size['size']):
                            result['models'][libcloud_region_name][size['size']] = {}
                            result['models'][libcloud_region_name][size['size']]['CPU'] = int(size['vCPU'])

                            if size['ECU'] == 'variable':
                                ecu = 0
                            else:
                                ecu = float(size['ECU'])

                            result['models'][libcloud_region_name][size['size']]['ECU'] = ecu

                            result['models'][libcloud_region_name][size['size']]['memoryGiB'] = float(size['memoryGiB'])

                            result['models'][libcloud_region_name][size['size']]['storageGB'] = size['storageGB']

                        result['prices'][libcloud_region_name][size['size']] = float(price)

        return result

    def update_ec2_pricing_file(self, pricing_file_path=None, pricing_data=None):
        """
        Update a json data file containing all known current AWS ec2 instance
        types and costs.
        """
        if not pricing_data:
            self._add_log('Scraping for ec2 pricing, can take a while..')
            pricing_data = self.scrape_ec2_pricing()

        data = {'compute': {}}
        data['updated'] = int(time.time())
        data['compute'].update(pricing_data)

        # Always sort the pricing info
        data = self.sort_nested_dict(data)

        if pricing_file_path:
            content = json.dumps(data, indent=4)
            lines = content.splitlines()
            lines = [line.rstrip() for line in lines]
            content = '\n'.join(lines)
            pricing_file_path = os.path.abspath(pricing_file_path)
            with open(pricing_file_path, 'w') as fp:
                fp.write(content)
        else:
            return data

    def santize_arguments(self, args):
        """Normalizes list of dictionary values to eliminate oddball inputs"""
        for key, val in args.items():
            # if we get passed in '' or "" then convert to empty string
            if val == "''" or val == '""':
                args[key] = ''
            # if we get passed in null or Null convert to None
            if val == 'null' or val == 'Null':
                args[key] = None
        return args
