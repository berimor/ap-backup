#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from pip.req import parse_requirements

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload -r local')
    sys.exit()

if sys.argv[-1] == 'register':
    os.system('python setup.py sdist register -r local')
    sys.exit()

setup( name='ap-backup'
     , version='master'
     , description='Describe this package in more detail here...'
     , author='Alexander Pikovsky'
     , author_email='alexander@pikovsky.com'
     , url='http://???'
     , download_url='http://???/repository/archive?ref=master#egg=deployment'
     , packages=[ 'ap_backup', ]
     , package_dir={'ap_backup': 'ap_backup'}
     , include_package_data=True
     , install_requires=[ str(r.req) for r in
                          parse_requirements(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt'), session='')
                        ]
     , license='ap Closed Source License'
     , zip_safe=False
     , keywords='ap-backup'
     , classifiers=[ 'Development Status :: 2 - Pre-Alpha'
                   , 'Intended Audience :: Developers'
                   , 'License :: optobee Closed Source License'
                   , 'Natural Language :: English'
                   , 'Programming Language :: Python :: 2'
                   , 'Programming Language :: Python :: 2.7'
                   , 'Programming Language :: Python :: Implementation :: PyPy'
                   ,
                   ]
     , scripts=[ 'scripts/ap-backup', 'scripts/ap-backup-checker', 'scripts/ap-multicopy' ]
     )