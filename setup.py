#!/usr/bin/env python
#
# Copyright 2011, Toru Maesaka
#
# Redistribution and use of this source code is licensed under
# the BSD license. See COPYING file for license description.

from distutils.core import setup

setup(
    author='Toru Maesaka',
    author_email='dev@torum.net',
    maintainer='Stephen Hamer',
    maintainer_email='stephen.hamer@upverter.com',
    name='python-kyototycoon',
    description='Kyoto Tycoon Client Library',
    version='0.4.10',
    license='BSD',
    keywords='Kyoto Tycoon, Kyoto Cabinet',
    packages=['kyototycoon'],
    requires=['percentcoding'],
    url='https://github.com/upverter/python-kyototycoon',
    zip_safe=False
)
