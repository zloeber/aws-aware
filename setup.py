#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""
from setuptools import setup, find_packages
with open('README.rst') as readme_file:
    readme = readme_file.read()
with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'boto3',
    'boto',
    'botocore',
    'datetime',
    'jinja2',
    'requests',
    'python-dotenv',
    'emails',
    'pyyaml',
    'urllib3',
    'figgypy',
    'seria',
    'xmltodict',
    'awscli',
]

setup_requirements = [ ]
test_requirements = [ ]

"""
files = [
    "config/*",
    "config/*/*",
    "commands/*",
    "logs/*",
    "templates/*"
]
"""

setup(
    author="Zachary Loeber",
    author_email='zloeber@gmail.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: DevOps',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
    ],
    description="Python module to check AWS instance counts for custom thresholds.",
    entry_points={
        'console_scripts': [
            'aws-aware=aws_aware.cli:main'
        ],
    },
    install_requires=requirements,
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='aws_aware',
    name='aws_aware',
    packages=find_packages(),
    #packages=find_packages(include=['aws_aware']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/zloeber/aws-aware',
    version='0.1.7',
    zip_safe=False,
)
