#!/usr/bin/env python
# coding: utf-8

"""
.. _print_example_configuration:

Script entry point provider to print out default configuration to aid in the
construction of a personnal configuration file.

Simply call this module from the command line and pipe it's output into a file
you will edit afterwards. For example::

    python -m VestaRestPackage.print_example_configuration > my_config_file.py
"""

from os.path import dirname, abspath, join

THIS_DIR = abspath(dirname(__file__))


def main():
    """
    Script entry point: Print out default configuration on standard out.
    """
    contents = open(join(THIS_DIR, 'default_configuration.py')).read()
    print(contents)

if __name__ == '__main__':
    main()
