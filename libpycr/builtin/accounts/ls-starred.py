"""List changes starred by one's account"""

# pylint: disable=invalid-name

import argparse
import logging

from libpycr.exceptions import PyCRError
from libpycr.gerrit.client import Gerrit
from libpycr.meta import GerritAccountBuiltin
from libpycr.pager import Pager
from libpycr.utils.commandline import expect_account_as_positional
from libpycr.utils.output import Formatter, NEW_LINE
from libpycr.utils.system import fail


class LsStarred(GerritAccountBuiltin):
    """Implement the LS-STARRED command"""

    # Logger for this command
    log = logging.getLogger(__name__)

    @property
    def name(self):
        return 'ls-starred'

    @property
    def description(self):
        return 'list starred changes'

    @staticmethod
    def tokenize(idx, change):
        """Token generator for the output

        Yields a stream of tokens: tuple of (Token, string).

        :param idx: index of the change in the list of changes to fetch
        :type idx: int
        :param change: the change
        :type change: ChangeInfo
        :yield: tuple[Token, str]
        """

        if idx:
            yield NEW_LINE

        for token in change.tokenize():
            yield token

    @staticmethod
    def parse_command_line(arguments):
        """Parse the LS-STARRED command command-line arguments

        Returns the account id that is provided on the command line. If no
        account is provided, returns None.

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: str
        """

        parser = argparse.ArgumentParser(
            description='List account starred changes')
        expect_account_as_positional(parser)

        cmdline = parser.parse_args(arguments)

        # fetch changes details
        return cmdline.account

    def run(self, arguments, *args, **kwargs):
        account_id = self.parse_command_line(arguments)

        try:
            changes = Gerrit.get_starred_changes(account_id or 'self')

        except PyCRError as why:
            fail('cannot list account starred changes', why)

        with Pager(command=self.name):
            for idx, change in enumerate(changes):
                print Formatter.format(self.tokenize(idx, change))
