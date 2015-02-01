"""List capabilities associated with one's account"""

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


class LsCapabilities(GerritAccountBuiltin):
    """Implement the LS-CAPABILITIES command"""

    # Logger for this command
    log = logging.getLogger(__name__)

    @property
    def name(self):
        return 'ls-capabilities'

    @property
    def description(self):
        return 'list capabilities'

    @staticmethod
    def parse_command_line(arguments):
        """Parse the LS-CAPABILITIES command command-line arguments

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: list[ChangeInfo]
        """

        parser = argparse.ArgumentParser(
            description='List account capabilities')
        expect_account_as_positional(parser)

        cmdline = parser.parse_args(arguments)

        # fetch changes details
        return cmdline.account

    def run(self, arguments, *args, **kwargs):
        account_id = self.parse_command_line(arguments)

        try:
            account = Gerrit.get_account(account_id or 'self')
            capabilities = Gerrit.get_capabilities(account_id or 'self')

        except PyCRError as why:
            fail('cannot list account capabilities', why)

        table = PrettyTable(['Capability', 'Value'])
        table.align['Capability'] = 'l'
        table.align['Value'] = 'c'

        table.add_row(['Administrate server',
                       checkmark(capabilities.administrate_server)])
        table.add_row(['Min Query limit', capabilities.query_limit.min])
        table.add_row(['Max Query limit', capabilities.query_limit.max])
        table.add_row(['Create account',
                       checkmark(capabilities.create_account)])
        table.add_row(['Create group', checkmark(capabilities.create_group)])
        table.add_row(['Create project',
                       checkmark(capabilities.create_project)])
        table.add_row(['Email reviewers',
                       checkmark(capabilities.email_reviewers)])
        table.add_row(['Kill task', checkmark(capabilities.kill_task)])
        table.add_row(['View caches', checkmark(capabilities.view_caches)])
        table.add_row(['Flush caches', checkmark(capabilities.flush_caches)])
        table.add_row(['View connections',
                       checkmark(capabilities.view_connections)])
        table.add_row(['View queue', checkmark(capabilities.view_queue)])
        table.add_row(['Run GC', checkmark(capabilities.run_gc)])

        with Pager(command=self.name):
            print 'Account: {}'.format(account.username)
            print table
