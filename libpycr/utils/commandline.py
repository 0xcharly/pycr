"""This module provides helper routines for manipulating the command-line"""


def expect_account_as_positional(cmdline_parser, multiple=False):
    """Add a new argument to the command-line parser (or sub-parser)

    Expect at most one positional argument.

    :param cmdline_parser: the command line parser
    :type cmdline_parser: argparse.ArgumentParser
    """

    cmdline_parser.add_argument(
        'account', metavar='ACCOUNT_ID', default=None,
        nargs='*' if multiple else '?', help='Gerrit Code Review Account-Id')


def expect_changes_as_positional(cmdline_parser):
    """Add a new argument to the command-line parser (or sub-parser)

    Expect at least one positional argument.

    :param cmdline_parser: the command line parser
    :type cmdline_parser: argparse.ArgumentParser
    """

    cmdline_parser.add_argument(
        'changes', metavar='CL', nargs='+',
        help='Gerrit Code Review CL / CL range / Change-Id')
