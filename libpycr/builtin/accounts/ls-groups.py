"""List all groups that contain the specified user as a member"""

# pylint: disable=invalid-name

import argparse
import logging

from libpycr.exceptions import PyCRError
from libpycr.gerrit.client import Gerrit
from libpycr.meta import GerritAccountBuiltin
from libpycr.pager import Pager
from libpycr.utils.commandline import expect_account_as_positional
from libpycr.utils.output import checkmark
from libpycr.utils.system import fail

from prettytable import PrettyTable


class LsGroups(GerritAccountBuiltin):
    """Implement the LS-GROUPS command"""

    # Logger for this command
    log = logging.getLogger(__name__)

    @property
    def name(self):
        return 'ls-groups'

    @property
    def description(self):
        return 'list groups'

    @staticmethod
    def parse_command_line(arguments):
        """Parse the LS-GROUPS command command-line arguments

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: list[ChangeInfo]
        """

        parser = argparse.ArgumentParser(description='List account groups')
        expect_account_as_positional(parser)

        cmdline = parser.parse_args(arguments)

        # fetch changes details
        return cmdline.account

    def run(self, arguments, *args, **kwargs):
        account_id = self.parse_command_line(arguments)

        try:
            groups = Gerrit.get_groups(account_id or 'self')

        except PyCRError as why:
            fail('cannot list account groups', why)

        table = PrettyTable(['Group', 'Description', 'Visible to all'])
        table.align = 'l'
        table.align['Visible to all'] = 'c'

        for group in groups:
            table.add_row([group.name, group.description or '',
                           checkmark(group.options.visible_to_all)])

        with Pager(command=self.name):
            print table
