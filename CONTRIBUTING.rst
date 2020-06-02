.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at <TBD>.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the BitBucket issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the BitBucket issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

EMR Bridge could always use more documentation, whether as part of the
official EMR Bridge docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://BitBucket.com/loza8001/aws_aware/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? Here's how to set up `aws_aware` for local development.

1. Fork the `aws_aware` repo on BitBucket.
2. Clone your fork locally
3. Install development environment::
   
   Using virtualenv::
    Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development.

    $ mkvirtualenv aws_aware
    $ cd aws_aware/
    $ python setup.py develop
    $ git checkout -b name-of-your-bugfix-or-feature

   Usinge pipenv(preferred)::
    Alternatively, you can use pipenv to setup the virtual environment from within the project directory after it has been cloned locally.

    $ cd aws_aware
    $ git checkout -b name-of-your-bugfix-or-feature
    $ pipenv install --dev
    $ pipenv install

    You can enter the environment with pipenv shell. Additionally, most modern editors like vscode will automatically detect pipenv and find the appropriate python virtual environment without further action.

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the
   tests, including testing other Python versions with tox::

    $ flake8 aws_aware tests
    $ python setup.py test
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Run the project from the cloned repository folder::
   You can make changes and then immediately run the aws_aware application locally if you like. This can be a nice way to get immediate feedback. From the project folder simply run the following:
   
   $ pip install -e . --user

   This can be run from Windows, Mac, or Linux and will create a wrapper executable around the aws_aware application which can be run at any time to launch the development version of this application.

7. Commit your changes and push your branch to BitBucket::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

8. Submit a pull request through the BitBucket website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in README.rst.
3. The pull request should work for Python 2.7, 3.4, 3.5 and 3.6. Make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests::

    $ python -m unittest tests.test_aws_aware

Deploying
---------

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in HISTORY.rst).

Then run::

$ git commit -m '0.x.x Release'
$ git push origin <branch>
$ bumpversion patch # possible: major / minor / patch
$ git push
$ git push --tags
$ make release

There are several make tasks available as well.

If you want to make the documentation via pandoc and sphinx::

$ make docs

If you just want to make the wheel file::

$ make dist

If you want to make the wheel file and push to artifactory::

$ make release