# -*- coding: utf-8 -*-
from os.path import abspath, join, split
import unittest

from ap_backup import AppConfig

__author__ = 'Alexander Pikovsky'


class Test(unittest.TestCase):

    def setUp(self):
        self.data_dir = abspath(join(split(__file__)[0], 'data'))

    def tearDown(self):
        pass

    def test_config(self):
        config = AppConfig(self.data_dir)
        pass

if __name__ == "__main__":
    unittest.main()

def suite():
    return unittest.TestLoader().loadTestsFromTestCase(Test)