#!/usr/bin/env python
# coding: utf-8

"""
Script entry point provider to print out default configuration to aid in the
construction of a personnal configuration file.
"""

from os.path import dirname, abspath, join

THIS_DIR = abspath(dirname(__file__))


def main():
    """
    Script entry point: Print out default configuration on standard out.
    """
    contents = open(join(THIS_DIR, 'default_configuration.py')).read()
    print contents

if __name__ == '__main__':
    main()
