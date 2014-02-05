"""
This module provides helper routines for manipulating the command-line.
"""


def expect_changes_as_positional(cmdline_parser):
    """
    Add a new argument to the command-line parser (or sub-parser).

    Expect at least one positional argument.

    PARAMETERS
        cmdline_parser: argparse.ArgumentParser
    """

    cmdline_parser.add_argument(
        'changes', metavar='CL', nargs='+',
        help='Gerrit Code Review CL / CL range / Change-Id')
