#!/usr/bin/env python3

from setuptools import setup, find_packages

from pathlib import Path
exec(open(Path("pagerduty", "version.py")).read())

try:
    long_description = open("README.md").read()
except IOError:
    long_description = ""

setup(
    name = 'pagerduty',
    version = VERSION,
    description = 'Library for the PagerDuty service API',
    long_description = long_description,
    author = 'Samuel Stauffer',
    author_email = 'samuel@playhaven.com',
    url = 'http://github.com/samuel/python-pagerduty',
    packages = find_packages(),
    license = "BSD",
    entry_points = {
        "console_scripts": [
            "pagerduty = pagerduty.command:main",
        ],
    },
    classifiers = [
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
