"""Rebase a change"""

import argparse
import logging

from libpycr.exceptions import NoSuchChangeError, PyCRError
from libpycr.gerrit.client import Gerrit
from libpycr.meta import GitClBuiltin
from libpycr.utils.output import Formatter, NEW_LINE, Token
from libpycr.utils.system import fail


class Rebase(GitClBuiltin):
    """Implement the REBASE command"""

    # Logger for this command
    log = logging.getLogger(__name__)

    @property
    def description(self):
        return 'rebase a change'

    @staticmethod
    def parse_command_line(arguments):
        """Parse the REBASE command command-line arguments

        Returns a tuple with a change_id and a revision_id.

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: str, str
        """

        parser = argparse.ArgumentParser(description='Rebase a change')
        parser.add_argument(
            'change_id', metavar='CL',
            help='Gerrit Code Review CL / CL range / Change-Id')

        cmdline = parser.parse_args(arguments)

        return cmdline.change_id

    @staticmethod
    def tokenize(change):
        """Token generator for the output

        Yields a stream of tokens: tuple of (Token, string).

        :param change: the change
        :type change: ChangeInfo
        :yield: tuple[Token, str]
        """

        for token in change.tokenize():
            yield token

        yield NEW_LINE
        yield NEW_LINE

        yield Token.Text, 'Change successfully rebased (new revision: '
        yield Token.Keyword, change.current_revision[:8]
        yield Token.Text, ')'

    def run(self, arguments, *args, **kwargs):
        change_id = self.parse_command_line(arguments)

        try:
            change = Gerrit.rebase(change_id)

        except NoSuchChangeError as why:
            self.log.debug(str(why))
            fail('invalid change')

        except PyCRError as why:
            fail('cannot rebase', why)

        print Formatter.format(Rebase.tokenize(change))
