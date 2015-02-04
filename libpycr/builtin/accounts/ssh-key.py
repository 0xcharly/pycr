"""Operate on SSH keys associated with one's account"""

# pylint: disable=invalid-name

import argparse
import logging
import os
import sys

from libpycr.exceptions import PyCRError
from libpycr.gerrit.client import Gerrit
from libpycr.meta import GerritAccountBuiltin
from libpycr.utils.commandline import expect_account_as_positional
from libpycr.utils.system import fail


class SshKey(GerritAccountBuiltin):
    """Implement the SSH-KEY command"""

    # Logger for this command
    log = logging.getLogger(__name__)

    subcommands = ('get', 'add', 'remove')

    @property
    def name(self):
        return 'ssh-key'

    @property
    def description(self):
        return 'manage ssh keys'

    @staticmethod
    def get_usage():
        """Return the command line usage for the SSH-KEY command

        :rtype: str
        """

        prog = os.path.basename(sys.argv[0])
        return os.linesep.join((
            'usage: %s [-h] {get,add,remove} ...' % prog,
            '',
            'Fetch, edit, delete ssh-key(s) from a user account',
            '',
            'positional arguments:',
            '  {get,add,remove}      available builtins',
            '    get                 display a ssh-key',
            '    add                 add a new ssh-key',
            '    remove              delete an existing ssh-key',
            '',
            'optional arguments:',
            '  -h, --help            show this help message and exit',
            ''
        ))

    @staticmethod
    def parse_command_line(arguments):
        """Parse the SSH-KEY command command-line arguments

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: Namespace
        """

        parser = argparse.ArgumentParser(description='Manage ssh key(s)')
        expect_account_as_positional(parser)

        actions = parser.add_subparsers(dest='cmd', help='available commands')
        get_cmd = actions.add_parser('get', help='Display SSH key details')
        get_cmd.add_argument('uuid', type=int, help='SSH key ID')

        cmdline = parser.parse_args(arguments)

        # fetch changes details
        return cmdline

    @staticmethod
    def run_get(arguments, *args, **kwargs):
        """???"""

        del args, kwargs

        parser = argparse.ArgumentParser(description='Display ssh key')
        parser.add_argument('account', type=str, help='account ID')
        parser.add_argument('uuid', type=int, help='SSH key ID')
        cmdline = parser.parse_args(arguments)

        try:
            key = Gerrit.get_ssh_key(cmdline.account, cmdline.uuid)

        except PyCRError as why:
            fail('cannot list account SSH keys', why)

        print key.ssh_public_key.strip()

    def run_add(self, arguments, *args, **kwargs):
        """???"""
        pass

    def run_remove(self, arguments, *args, **kwargs):
        """???"""
        pass

    def run(self, arguments, *args, **kwargs):
        if not arguments:
            fail('No command given.')

        command = arguments[0]
        arguments = arguments[1:]

        if command in ('-h', '--help'):
            sys.exit(self.get_usage())

        if command not in self.subcommands:
            fail('Unknown subcommand: {}'.format(command))

        if command == 'get':
            self.run_get(arguments, *args, **kwargs)
        elif command == 'add':
            self.run_add(arguments, *args, **kwargs)
        elif command == 'remove':
            self.run_remove(arguments, *args, **kwargs)
