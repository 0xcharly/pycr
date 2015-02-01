"""Submit a change"""

import argparse
import logging

from libpycr.exceptions import NoSuchChangeError, PyCRError
from libpycr.gerrit.client import Gerrit
from libpycr.meta import GitClBuiltin
from libpycr.utils.output import Formatter, Token, NEW_LINE
from libpycr.utils.system import fail


class Submit(GitClBuiltin):
    """Implement the SUBMIT command"""

    # Logger for this command
    log = logging.getLogger(__name__)

    @property
    def description(self):
        return 'submit a change'

    @staticmethod
    def parse_command_line(arguments):
        """Parse the SUBMIT command command-line arguments

        Returns a tuple with a change_id and a revision_id.

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: str, str
        """

        parser = argparse.ArgumentParser(description='Submit a change.')
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

        yield Token.Text, 'Change successfully merged (revision: '
        yield Token.Keyword, change.current_revision[:8]
        yield Token.Text, ')'

    def run(self, arguments, *args, **kwargs):
        change_id = Submit.parse_command_line(arguments)

        try:
            change = Gerrit.get_change(change_id)

            if not Gerrit.submit(change.uuid):
                fail('submit could not be merged')

        except NoSuchChangeError as why:
            self.log.debug(str(why))
            fail('invalid change')

        except PyCRError as why:
            fail('cannot submit', why)

        print Formatter.format(Submit.tokenize(change))
