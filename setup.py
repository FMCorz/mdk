#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Moodle Development Kit

Copyright (c) 2014 Frédéric Massart - FMCorz.net

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

http://github.com/FMCorz/mdk
"""

import os
from setuptools import setup, find_packages

# Load version number.
execfile('mdk/version.py')

# Get the long description from the relevant file.
longDescription = ''
with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as f:
    longDescription = f.read()

# Load the requirements.
requirements = []
with open('requirements.txt') as f:
    requirements = f.readlines()

# Get the content of the scripts folder.
scripts = []
for f in os.listdir(os.path.join(os.path.dirname(__file__), 'mdk', 'scripts')):
    if f == 'README.rst':
        continue
    scripts.append('scripts/%s' % (f))

setup(
    name='moodle-sdk',
    version=__version__,
    description='Moodle Development Kit',
    long_description=longDescription,
    license='MIT',

    url='https://github.com/FMCorz/mdk',
    author='Frédéric Massart',
    author_email='fred@fmcorz.net',
    classifiers=[
        'Development Status :: 6 - Mature',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: Education',
        'Topic :: Software Development',
        'Topic :: Utilities'
    ],
    keywords='mdk moodle moodle-sdk',

    packages=find_packages(),
    package_data={'mdk': ['config-dist.json'] + scripts},
    install_requires=requirements,
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'mdk = mdk.__main__:main'
        ]
    }
)
