#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Get math mode environments from text file."""

import os
import re


def main(filename):
    math_mode = get_math_mode(filename)
    for el in math_mode:
        print(el)


def get_math_mode(filename):
    """
    Read `filename` and get all math mode contents from it.

    Parameters
    ----------
    filename : str
        Path to a TeX file

    Returns
    -------
    list of math mode contents
    """
    with open(filename) as f:
        lines = f.read()
    p1 = re.compile('\$(.+?)\$')
    p2 = re.compile('\\[(.+?)\\\]')
    matches = p1.findall(lines)
    matches += p2.findall(lines)
    return matches


def unfold_math(expression):
    tree = {}
    return tree


def is_valid_file(parser, arg):
    """Check if arg is a valid file that already exists on the file
       system.
    """
    arg = os.path.abspath(arg)
    if not os.path.exists(arg):
        parser.error("The file %s does not exist!" % arg)
    else:
        return arg


def get_parser():
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("-f", "--file",
                        dest="filename",
                        type=lambda x: is_valid_file(parser, x),
                        help="write report to FILE",
                        metavar="FILE")
    return parser


if __name__ == "__main__":
    args = get_parser().parse_args()
    main(args.filename)
