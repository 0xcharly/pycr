"""List diff preferences associated with one's account"""

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


class LsDiffPrefs(GerritAccountBuiltin):
    """Implement the LS-DIFF-PREFS command"""

    # Logger for this command
    log = logging.getLogger(__name__)

    @property
    def name(self):
        return 'ls-diff-prefs'

    @property
    def description(self):
        return 'list diff preferences'

    @staticmethod
    def parse_command_line(arguments):
        """Parse the LS-DIFF-PREFS command command-line arguments

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: list[ChangeInfo]
        """

        parser = argparse.ArgumentParser(
            description='List account diff preferences')
        expect_account_as_positional(parser)

        cmdline = parser.parse_args(arguments)

        # fetch changes details
        return cmdline.account

    def run(self, arguments, *args, **kwargs):
        account_id = self.parse_command_line(arguments)

        try:
            account = Gerrit.get_account(account_id or 'self')
            prefs = Gerrit.get_diff_prefs(account_id or 'self')

        except PyCRError as why:
            fail('cannot list account diff preferences', why)

        table = PrettyTable(['Preference', 'Value'])
        table.align['Preference'] = 'l'
        table.align['Value'] = 'c'

        table.add_row(['Context', prefs.context])
        table.add_row(['Expand all comments',
                       checkmark(prefs.expand_all_comments)])
        table.add_row(['Ignore whitespace', prefs.ignore_whitespace])
        table.add_row(['Intraline difference',
                       checkmark(prefs.intraline_difference)])
        table.add_row(['Line length', prefs.line_length])
        table.add_row(['Manual review', checkmark(prefs.manual_review)])
        table.add_row(['Retain header', checkmark(prefs.retain_header)])
        table.add_row(['Show line endings',
                       checkmark(prefs.show_line_endings)])
        table.add_row(['Show tabs', checkmark(prefs.show_tabs)])
        table.add_row(['Show whitespace errors',
                       checkmark(prefs.show_whitespace_errors)])
        table.add_row(['Skip deleted', checkmark(prefs.skip_deleted)])
        table.add_row(['Skip uncommented', checkmark(prefs.skip_uncommented)])
        table.add_row(['Syntax highlighting',
                       checkmark(prefs.syntax_highlighting)])
        table.add_row(['Tab size', prefs.tab_size])

        with Pager(command=self.name):
            print 'Account: {}'.format(account.username)
            print table
