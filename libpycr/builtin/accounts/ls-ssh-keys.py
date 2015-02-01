"""List SSH keys associated with one's account"""

# pylint: disable=invalid-name

import argparse
import logging

from libpycr.exceptions import PyCRError
from libpycr.gerrit.client import Gerrit
from libpycr.meta import GerritAccountBuiltin
from libpycr.pager import Pager
from libpycr.utils.commandline import expect_account_as_positional
from libpycr.utils.system import fail

from prettytable import PrettyTable


class LsSshKeys(GerritAccountBuiltin):
    """Implement the LS-SSH-KEYS command"""

    # Logger for this command
    log = logging.getLogger(__name__)

    @property
    def name(self):
        return 'ls-ssh-keys'

    @property
    def description(self):
        return 'list ssh key(s)'

    @staticmethod
    def parse_command_line(arguments):
        """Parse the LS-SSH-KEYS command command-line arguments

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: list[ChangeInfo]
        """

        parser = argparse.ArgumentParser(description='List account ssh key(s)')
        expect_account_as_positional(parser)

        cmdline = parser.parse_args(arguments)

        # fetch changes details
        return cmdline.account

    def run(self, arguments, *args, **kwargs):
        account_id = self.parse_command_line(arguments)

        try:
            account = Gerrit.get_account(account_id or 'self')
            keys = Gerrit.get_ssh_keys(account_id or 'self')

        except PyCRError as why:
            fail('cannot list account SSH keys', why)

        table = PrettyTable(
            ['Id', 'Algorithm', 'Comment', 'Valid', 'Encoded key'])
        table.align = 'l'

        for key in keys:
            table.add_row([key.seq, key.algorithm, key.comment,
                           u'\u2713' if key.valid else u'\u2717',
                           key.encoded_key])

        with Pager(command=self.name):
            print 'Account: {}'.format(account.username)
            if keys:
                print table
            else:
                print 'No SSH keys'
