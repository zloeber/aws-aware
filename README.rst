AWS-Aware - AWS Instance Threshold Monitor
------------------------------------------

AWS Instance threshold monitoring bot.

Description
-----------

This app manually polls AWS for ec2 instance information based on tags,
saves all data into a local file (cache), then uses that cached data to
generate per team/environment instance threshold notifications that emit
nice html reports based on tag filters.

Requirements
------------

I ran into issues installing dependencies (specifically psutil) without
installing the following system library:

.. code:: bash

   sudo apt install python3-dev

Install
-------

All install options assume you will be targeting a user or virtual
python environment because that’s the wise way to manage your local
packages right?

**Install For Development**

Clone this repo then jump into it:

.. code:: bash

   git clone ssh://git@github.com/zloeber/aws-aware
   cd aws-aware

Install locally so that the installed binary is simply a shell for
calling the files within the current folder. This allows for you to run
the cli interactively while developing this app:

.. code:: bash

   pip install -f requirements.txt --user
   pip install -e . --user

Or on a Linux/Mac with Python and pip installed:

.. code:: bash

   make install-deps install-local

**Install Locally (Preferred)**

Install from some custom artifactory via pip to the user workspace:

.. code:: bash

   pip install aws-aware --user --extra-index-url https://pypi.contoso.com/artifactory/api/pypi/internal-pypi-server/simple

You can create your own virtual environment to install this module as
well using pipenv or virtualenvwrapper.

.. code:: bash

   pip install pipenv --user
   cd aws-aware
   pipenv install
   pipenv shell

Calling the script in a virtual environment may prevent the script from
being able to be run concurrently though and should not be used in
production (unless possibly in a virtualenv within a container).

Initialization
--------------

Easy! Copy ``./config/deploy.env`` to ``./config/team1.env`` then
initialize a new aws-aware configuration file:

.. code:: bash

   make app/config/init dpl=./config/team1.env

After running this you will end up with a configuration file that you
defined in ``./config/team1-config.yml`` as well as a
``./config/team1-monitor.yml`` config. Both can then be used moving
forward to generate alerts for team1 (these config files are also able
to be upgraded if the app upgrades for any reason).

You can then run other make tasks using the same configuration file:

.. code:: bash

   # Run an instance debug export based on the previously created config file
   make app/config/show dpl=team1.env

..

   **NOTE:** aws-aware supports exporting configuration to self-updating
   configuration as code! ``make app/config/export dpl=team1.env``

Upgrade
-------

Upgrading is similar to the initial install:

.. code:: bash

   pip install aws-aware --user --extra-index-url https://pypi.contoso.com/artifactory/api/pypi/internal-pypi-server/simple -U

Or to force re-install:

.. code:: bash

   pip install aws-aware --user --extra-index-url https://pypi.contoso.com/artifactory/api/pypi/internal-pypi-server/simple -U --no-cache-dir -I

If you are upgrading the package then it is important to run the config
file upgrade operation against any of your config files to validate if
any new, pertinant, configuration entries have been added between
versions. Upgrade with the following:

.. code:: bash

   aws-aware config upgradeconfig

   # Or against your custom configuration file
   aws-aware -configfile awsaware-globalconfig.yml config upgradeconfig

Usage
-----

The script uses the Python click module for parsing CLI arguments. This
makes it very similar to the tower-cli command line tool in usage.

   **NOTE:** If running this script under bash (via WSL, or on
   Linux/Mac) you can enable command line autocompletion with the
   following command in your bash profile:
   ``eval "$(_AWS_AWARE_COMPLETE=source aws-aware)"``

As such it is critical to be aware that using the context sensitive help
within the cli itself is preferred to this documentation as it will
always contain the most recent features and flags. All remaining
documentation is for general reference and getting started.

Configuration
-------------

The first time aws-aware is run, it will create a global configuration
file to use automatically within its own install location (usually
$HOME/.local/bin). You can (and should) use an alternate script
configuration file by passing it first as ``-configfile`` so that the
global configuration is not bound to the default install path pip uses
for the module. You can create a new default configuration file to use
via the new sub-command.

You can view your current configuration in any editor or via this
command:

.. code:: bash

   aws-aware config show

   # Or against your custom configuration file
   aws-aware -configfile awsaware-globalconfig.yml config show

..

   **IMPORTANT** If this is your first time installing the application
   it would be wise to create a new global configuration file and
   working job directory within a secured location then commit the file
   to your repo (Config as code). This is almost mandatory if the app is
   installed and used in a shared environment.

Monitors
--------

By default, no instance monitoring is performed. In order to monitor on
instance count you will need to define them declaratively in a
monitoring config yaml file. Below is an example of
``config/prodenv-monitors.yml`` that one might use to monitor production
instances of types ‘i2.xlarge’ and ‘r3.4xlarge’.

.. code:: yaml

   # Monitor Configuration File for aws-aware
   view:
     instance_tags: ['ClusterName', 'Environment', 'Location', 'Name', 'OS', 'PatchDay', 'Purpose', 'Stack']
     instance_state: ['running']
     notice_columns: ['ClusterName', 'Environment', 'Name', 'Stack']
     # Tags on the left get transposed to column headers on the right
     column_lookup:
       ClusterName: 'Cluster Name'
       instance_type: 'Instance Type'
       Environment: 'Env'
       launch_time: 'Launched'
       public_ip_address: 'Public IP'
       private_ip_address: 'Private IP'
       name: 'Name'
   filters:
     Environment: 'Production'
   monitors:
     - name: i2.xlarge
       thresholdtype: instance
       warningthreshold: 0
       alertthreshold: 1
       enabled: true
     - name: r3.4xlarge
       thresholdtype: instance
       warningthreshold: 0
       alertthreshold: 1
       enabled: true

Uninstalling
------------

.. code:: bash

   pip uninstall aws-aware

Logging
-------

Logging is not enabled by default. If you need additional insight on
what is going on for a job you will need to enable logging in the
config/config.yml file. Relevant configuration settings are:

::

   loggingenabled: false
   loglevel: "INFO"
   logpath: "logs/"
   logfile: "runtime.log"
   logformat: "%(relativeCreated)6d %(threadName)s %(message)s"

Simply set loggingenabled to true and run the script again to get log
output in the logs/runtime.log file (for long running jobs
``tail -f logs/runtime.log``). This will emit logs for AWS and other
calls.

Email Notifications
-------------------

If warningnotice or alertnotice flags are sent to aws-aware and either
thresholds have been reached for any monitor then an alert will be sent
to any defined emailrecipients.

Slack Notifications
~~~~~~~~~~~~~~~~~~~

**NOTE:** This is barely tested at all.

Notifications can alternatively be sent to a Slack channel via a
webhook. You can add a webhook for your channel `at the slack api
site <https://get.slack.help/hc/en-us/articles/115005265063-Incoming-WebHooks-for-Slack#set-up-incoming-webhooks>`__

You can then add one or multiple hooks into your global configuration
file in the slack_webhooks array. Then change slack_notifications to
True. Once this has been done anytime a notification is triggered so too
will each of the slack channels receive notifications.

AWS SSO
~~~~~~~

To use SSO based authentication you will need to ensure your existing
credential file exists and has a dedicated profile to use. In this case,
we will use the profile called ‘saml’ to maintain our session token
information once authenticated via ADFS/SSO.

.. code:: bash

   mkdir -p ${HOME}/.aws/credentials
   echo '[saml]' >> ${HOME}/.aws/credentials

Then clone the following project or use something similar to it for saml
authentication updates to your local aws credentials file:

.. code:: bash

   export ARG_USERNAME=consultant@contoso.com
   export ARG_USERPASS='Lan ID Password'
   make sso-login

This will call a python script that will use the passed env vars to
attempt to perform sso authentication then update the local saml profile
with token/session information within the profile. You can use the
script within (aws-sso.py) stand-alone to update a local aws profile for
SAML authentication (tested as working on Windows/Mac/Linux with Python
2.7 only).

   **NOTE** Be careful to only specify dedicated profile names when
   using this script or you risk overwriting local ~/.aws/credentials
   information that other projects may depend upon. Default profile it
   will target is ``saml``.

CI Steps
--------

Some common CI steps for this project includes:

.. code:: bash

   # Code coverage reports
   make coverage

   # Code linting reports
   make lint

   # Unit test reports
   make tests

   # Test against all versions of python via tox
   make test-all

   # Update documentation
   make docs

More information on developing this project be found in the contribution
document.

CD Steps
--------

This is a quick list of steps to fully update and publish this project
to Artifactory.

To start you will need to modify your ``${HOME}\.pypirc`` profile to
look similar to the following:

.. code:: bash

   [distutils]
   index-servers = internal-pypi-server
   [internal-pypi-server]
   repository: https://pypi.contoso.com/artifactory/api/pypi/internal-pypi-server
   username: <id>
   password: <password>

You will want to run this from an os with the make utility
(alternatively pull out the commands from the Makefile and manually run
them)

1. First update HISTORY.rst with notes on your updates.
2. Then run the following if you are releasing a new release:

.. code:: bash

   make docs
   git add .
   git commit -m '0.2.x Release'
   bumpversion patch
   git push origin master
   git push --tags
   make release

Or, run the following to update the current release:

.. code:: bash

   make docs
   git add .
   git commit -m '0.2.x Release'
   git push origin master
   make release

Credits
-------

More than this I’m sure but here is how the project was bootstraped:

`Cookiecutter: <https://github.com/audreyr/cookiecutter>`__

`elgertam/cookiecutter-pipenv: <https://github.com/elgertam/cookiecutter-pipenv>`__

`audreyr/cookiecutter-pypackage: <https://github.com/audreyr/cookiecutter-pypackage>`__
