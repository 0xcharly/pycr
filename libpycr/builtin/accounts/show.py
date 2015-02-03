"""Display the account(s) details"""

import argparse
import logging

from libpycr.exceptions import PyCRError
from libpycr.gerrit.client import Gerrit
from libpycr.meta import GerritAccountBuiltin
from libpycr.pager import Pager
from libpycr.utils.commandline import expect_account_as_positional
from libpycr.utils.system import fail

from prettytable import PrettyTable


class Show(GerritAccountBuiltin):
    """Implement the SHOW command"""

    # Logger for this command
    log = logging.getLogger(__name__)

    @property
    def description(self):
        return 'show account'

    @staticmethod
    def parse_command_line(arguments):
        """Parse the SHOW command command-line arguments

        Returns the account id that is provided on the command line. If no
        account is provided, returns None.

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: str
        """

        parser = argparse.ArgumentParser(description='Show account(s) details')
        expect_account_as_positional(parser, multiple=True)

        cmdline = parser.parse_args(arguments)

        # fetch changes details
        return cmdline.account

    def run(self, arguments, *args, **kwargs):
        account_ids = self.parse_command_line(arguments)

        try:
            accounts = (Gerrit.get_account(a) for a in account_ids or ['self'])

        except PyCRError as why:
            fail('cannot list accounts', why)

        table = PrettyTable(['Username', 'Name', 'Email'])
        table.align = 'l'

        for account in set(accounts):
            table.add_row([account.username, account.name, account.email])

        with Pager(command=self.name):
            print table
