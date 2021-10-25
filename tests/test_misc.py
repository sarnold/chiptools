import unittest
import os
import logging
import sys

import pytest

from chiptools import __version__
from chiptools.common.utils import create_parser, self_test


testroot = os.path.dirname(__file__) or '.'
sys.path.insert(0, os.path.abspath(os.path.join(testroot, os.path.pardir)))


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.parser = create_parser()

    def test_parser(self):
        parsed = self.parser.parse_args(['--version', '--test'])
        self.assertTrue(parsed.version)
        self.assertTrue(parsed.test)


class SelfTest(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def _pass_fixtures(self, capsys):
        self.capsys = capsys

    def test_self_check(self):
        self_test()
        captured = self.capsys.readouterr()
        self.assertIn('PASSED', captured.out)
