"""Display the list of changes given the input criterion"""

import argparse
import logging

from libpycr.exceptions import QueryError, PyCRError
from libpycr.gerrit.client import Gerrit
from libpycr.meta import GitClBuiltin
from libpycr.pager import Pager
from libpycr.utils.output import Formatter, NEW_LINE
from libpycr.utils.system import fail


class List(GitClBuiltin):
    """Implement the LIST command"""

    # Logger for this command
    log = logging.getLogger(__name__)

    @property
    def description(self):
        return 'list change(s)'

    @staticmethod
    def parse_command_line(arguments):
        """Parse the LIST command command-line arguments

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: str, str, bool
        """

        parser = argparse.ArgumentParser(
            description='List changes by owner and status')
        parser.add_argument(
            '--status', default='open', choices=Gerrit.get_all_statuses(),
            help='the status of the changes (default: open)')

        exclusive = parser.add_mutually_exclusive_group()
        exclusive.add_argument(
            '--owner', default='self',
            help='the owner of the changes (default: self)')
        exclusive.add_argument(
            '--watched', default=False, action='store_true',
            help='list only watched changes')

        cmdline = parser.parse_args(arguments)

        # Fetch changes details
        return cmdline.owner, cmdline.status, cmdline.watched

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

    def run(self, arguments, *args, **kwargs):
        owner, status, watched = self.parse_command_line(arguments)

        try:
            if watched:
                changes = Gerrit.list_watched_changes(status=status)
            else:
                changes = Gerrit.list_changes(status=status, owner=owner)

        except QueryError as why:
            # No result, not an error
            self.log.debug(str(why))
            return

        except PyCRError as why:
            fail('cannot list changes', why)

        with Pager(command=self.name):
            for idx, change in enumerate(changes):
                print Formatter.format(self.tokenize(idx, change))
