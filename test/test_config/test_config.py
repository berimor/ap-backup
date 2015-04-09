# -*- coding: utf-8 -*-
from os import path
import unittest

from ap_backup import AppConfig

__author__ = 'Alexander Pikovsky'


class Test(unittest.TestCase):

    def setUp(self):
        self.data_dir = path.abspath(path.join(path.dirname(__file__), 'data'))

    def tearDown(self):
        pass

    def test_config(self):
        config_file = path.join(self.data_dir, "config.yaml")
        config = AppConfig(config_file)
        pass

if __name__ == "__main__":
    unittest.main()

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(Test)