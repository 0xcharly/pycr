"""Low level routines used by this tool for command line processing"""

import argparse
import logging
import sys

from libpycr import get_version
from libpycr.http import RequestFactory
from libpycr.utils.introspect import get_all_subclasses
from libpycr.utils.output import Formatter

# pylint: disable=W0401
# Disable "Wildcard import"
from libpycr.builtin import *  # NOQA


def build_cmdline_parser(builtin_type):
    """Build and return the command-line parser to use

    :param builtin_type: the type of Builtin to look for
    :type builtin_type: Builtin
    :rtype: argparse.ArgumentParser
    """

    # Create the parser object
    parser = argparse.ArgumentParser(
        description='Gerrit Code Review command line tools')

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
        '--username', default=None,
        help='Gerrit Code Review HTTP digest authentication')

    # Hidden argument to select a custom Pygments formatter.
    # This is not a very user-friendly feature so do not litter the usage
    # message with it.
    parser.add_argument(
        '--formatter', default='terminal256',
        choices=sum([f.aliases for f in Formatter.get_all()], []),
        help=argparse.SUPPRESS)

    # Register builtins
    actions = parser.add_subparsers(dest='builtins', help='available builtins')

    # HELP command
    cl_help = actions.add_parser(
        'help', help='display help information about %(prog)s builtins')
    cl_help.add_argument(
        'builtin', nargs='?', help='display help for that builtin')

    # Register all builtins
    for cmd_class in get_all_subclasses(builtin_type):
        cmd = cmd_class()
        subparser = actions.add_parser(cmd.name, add_help=False,
                                       help=cmd.description)
        subparser.set_defaults(command=cmd)

    return parser


def display_help(builtin_type, cmd_name=None):
    """Display the help message

    This includes the program usage and information about the arguments.

    :param builtin_type: the type of Builtin to look for
    :type builtin_type: Builtin
    :param cmd_name: optional command name for which to display the help
        message. Displays the program-wide help if None.
    :type cmd_name: str
    """

    parser = build_cmdline_parser(builtin_type)

    if cmd_name is None:
        # %(prog)s --help case
        sys.exit(parser.format_help())

    else:
        cmdline = parser.parse_args([cmd_name])

        if cmdline.command:
            # %(prog)s help assign
            cmdline.command.run(['--help'])
        else:
            # %(prog)s help --help case
            parser.parse_args([cmd_name, '--help'])


def parse_command_line(builtin_type):
    """Parse the command-line arguments

    Returns a tuple containing the action to execute, and the arguments to use
    with that action.

    :param builtin_type: the type of Builtin to look for
    :type builtin_type: Builtin
    :rtype: Function, list[str]
    """

    parser = build_cmdline_parser(builtin_type)

    # Parse the command-line
    cmdline, remaining = parser.parse_known_args(sys.argv[1:])

    # Activate logging if requested
    if cmdline.debug:
        logging.basicConfig(
            format='[%(asctime)s %(name)-20s] %(message)s', datefmt='%H:%M:%S',
            level=logging.DEBUG)

    # Display help if requested (display_help exits the program)
    if cmdline.builtins == 'help':
        display_help(builtin_type, cmdline.builtin)

    # Configure the HTTP request engine
    RequestFactory.set_unsecure_connection(cmdline.unsecure)

    if cmdline.username is not None:
        # Reset the pair (username, password) if --username is supplied on the
        # command line. The user will be prompted its password.
        RequestFactory.set_auth_token(cmdline.username, None)

    return cmdline.command, remaining
