#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from VestaRestPackage.__meta__ import API_VERSION, __author__, __contact__

with open('README.rst') as readme_file:
    README = readme_file.read()

if os.path.exists("HISTORY.rst"):
    with open('HISTORY.rst') as history_file:
        HISTORY = history_file.read().replace('.. :changelog:', '')
else:
    HISTORY = ""

REQUIREMENTS = [
    "Flask==0.10.1",
    "pyrabbit==1.0.1",
    "PyJWT==0.4.3",
    "python-novaclient",
    "dicttoxml==1.6.6",
    "VestaService==0.2.2",
    "configparser",
    "future"
]

TEST_REQUIREMENTS = [
    'nose'
]

setup(
    # -- meta information --------------------------------------------------
    name='VestaRestPackage',
    version=API_VERSION,
    description="Code to facilitate creation of Vesta Service Gateway.",
    long_description=README + '\n\n' + HISTORY,
    author=__author__,
    author_email=__contact__,
    url='https://github.com/crim-ca/RESTPackage',
    platforms=['linux_x86_64'],
    license="Apache 2.0",
    keywords='Vesta,Service, ServiceGateway',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],

    # -- Package structure -------------------------------------------------
    packages=[
        'VestaRestPackage'
    ],
    package_dir={'VestaRestPackage': 'VestaRestPackage'},
    package_data={'VestaRestPackage': ['static/*', 'templates/*']},

    install_requires=REQUIREMENTS,
    zip_safe=False,

    # -- self - tests --------------------------------------------------------
    test_suite='tests',
    tests_require=TEST_REQUIREMENTS,

    entry_points={
        'console_scripts':
            ['vrp_default_config='
             'VestaRestPackage.print_example_configuration:main']}
)
