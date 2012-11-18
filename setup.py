#!/usr/bin/env python

from setuptools import setup

setup(
    name = 'node_tree',
    version = '0.1.0',

    description = 'Tree class, where nodes can be referenced by path tuple '\
            'or linear, 0-based index.',
    author = 'Christian Fobel',
    author_email = 'christian@fobel.net',
    license = 'GPLv2',
    packages=['node_tree'],
    url = 'https://github.com/cfobel/python___node_tree',

    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
