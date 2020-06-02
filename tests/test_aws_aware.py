#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `aws_aware` package."""


import unittest
from click.testing import CliRunner

from aws_aware import aws_aware
from aws_aware import cli


class TestAws_aware(unittest.TestCase):
    """Tests for `aws_aware` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_init_default_config(self):
        """Initialize a configuration file if one does not exist."""
    
    def test_001_load_default_config(self):
        """Load the default configuration file"""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'Result okay' in str(result)
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert 'Result okay' in str(help_result)
