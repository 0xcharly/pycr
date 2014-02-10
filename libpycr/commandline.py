"""
This module contains the low level routines used by this tool for command line
processing.
"""

import argparse
import logging
import sys

from libpycr import get_version
from libpycr.commands import assign, show
from libpycr.commands import list as list_command
from libpycr.http import RequestFactory
from libpycr.utils.output import Formatter


def build_cmdline_parser():
    """
    Build and return the command-line parser to use.

    RETURNS
        argparse.ArgumentParser
    """

    # Create the parser object
    parser = argparse.ArgumentParser(
        description='Gerrit Code Review Command-line.')

    parser.add_argument(
        '--version', action='version',
        version='%(prog)s version ' + get_version())

    # Activate debug logging. Do not provide this option in usage message
    parser.add_argument(
        '--debug', default=False, action='store_true', help=argparse.SUPPRESS)

    # Whether to use HTTP instead of HTTPS to connect to the remote
    parser.add_argument(
        '--unsecure', default=False, action='store_true',
        help='prefer HTTP over HTTPS (disabled by default)')

    # Username to use for authentication.
    # If provided, override the configuration file's value(s) and reset the
    # password to None (the user will be prompted the password at runtime).
    parser.add_argument(
        '--username', default=None, help='Gerrit Code Review authentication')

    # Disable colored output (using the internal formatter mechanism)
    parser.add_argument(
        '--no-color', default=False, action='store_true',
        help='disable colored output')

    # Hidden argument to select a custom Pygments formatter.
    # This is not a very user-friendly feature so do not litter the usage
    # message with it.
    parser.add_argument(
        '--formatter', default='terminal256',
        choices=sum([f.aliases for f in Formatter.get_all()], []),
        help=argparse.SUPPRESS)

    # Register sub-commands
    actions = parser.add_subparsers(
        dest='subcommand', help='available subcommands')

    # HELP command
    cl_help = actions.add_parser(
        'help', help='display help information about %(prog)s sub-commands')
    cl_help.add_argument(
        'command', nargs='?', help='display help for that command')

    # LIST command
    cl_list = actions.add_parser('list', help='list change(s)')
    cl_list.set_defaults(command=list_command.main)

    # SHOW command
    cl_show = actions.add_parser(
        'show', help='display code reviews for change(s)')
    cl_show.set_defaults(command=show.main)

    # ASSIGN command
    cl_assign = actions.add_parser(
        'assign', prefix_chars='-+', help='assign reviewer to change(s)')
    cl_assign.set_defaults(command=assign.main)

    return parser


def display_help(command=None):
    """
    Display the help message, including the program usage and information about
    the arguments.

    PARAMETERS
        command: optional command for which to display the help message.
            displays the program-wide help if None.
    """

    parser = build_cmdline_parser()

    if command is None:
        # cl --help case
        sys.exit(parser.format_help())

    else:
        cmdline = parser.parse_args([command])

        if cmdline.command:
            # cl help assign
            cmdline.command(['--help'])
        else:
            # cl help --help case
            parser.parse_args([command, '--help'])


def parse_command_line(argv):
    """
    Parse the command-line arguments, and return a tuple containing the action
    to execute, and the arguments to use with that action.

    PARAMETERS
        argv: the argument array to parse

    RETURNS
        a tuple containing both the command callback to execute and any
        remaining arguments that need more parsing.
    """

    parser = build_cmdline_parser()

    # Parse the command-line
    cmdline, remaining = parser.parse_known_args(argv[1:])

    # Activate logging if requested
    if cmdline.debug:
        logging.basicConfig(
            format='[%(asctime)s %(name)-20s] %(message)s', datefmt='%H:%M:%S',
            level=logging.DEBUG)

    # Display help if requested (display_help exits the program)
    if cmdline.subcommand == 'help':
        display_help(cmdline.command)

    # Configure the HTTP request engine
    RequestFactory.set_unsecure_connection(cmdline.unsecure)

    if cmdline.username is not None:
        # Reset the pair (username, password) if --username is supplied on the
        # command line. The user will be prompted its password.
        RequestFactory.set_auth_token(cmdline.username, None)

    # Configure the program output
    if cmdline.no_color:
        Formatter.set_formatter(Formatter.NO_COLOR)
    else:
        Formatter.set_formatter(cmdline.formatter)

    return cmdline.command, remaining
