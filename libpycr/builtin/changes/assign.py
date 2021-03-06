"""Assign one or more reviewers to one or more Gerrit CL"""

import os
import sys

from libpycr.exceptions import PyCRError
from libpycr.gerrit.changes import fetch_change_list_or_fail
from libpycr.gerrit.client import Gerrit
from libpycr.meta import GitClBuiltin
from libpycr.utils.output import Formatter, NEW_LINE, Token
from libpycr.utils.system import fail, warn


class Assign(GitClBuiltin):
    """Implement the ASSIGN command"""

    @property
    def description(self):
        return 'add/delete reviewer to/from change(s)'

    @staticmethod
    def display_help():
        """Display the help for this command and exit

        We have to forge our own help output because we do not use the argparse
        module to parse the command-line arguments.
        """

        buf = [('usage: %s assign [-h] CL [CL ...] '
                '[+/-REVIEWER [+/-REVIEWER ...]]')]
        buf.append('')
        buf.append('Add or delete reviewer(s) to one or more changes')
        buf.append('')
        buf.append('positional arguments:')
        buf.append(('  CL             '
                    'Gerrit Code Review CL / CL range / Change-Id'))
        buf.append('  +REVIEWER      add REVIEWER to the change')
        buf.append('  -REVIEWER      delete REVIEWER from the change')
        buf.append('')
        buf.append('optional arguments:')
        buf.append('  -h, --help     show this help message and exit')

        print os.linesep.join(buf) % os.path.basename(sys.argv[0])
        sys.exit()

    @staticmethod
    def parse_command_line(arguments):
        """Parse the SHOW command command-line arguments

        Returns a tuple containing three lists:
                - the list of ChangeInfo
                - the list of reviewers to add
                - the list of reviewers to delete

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: tuple[ChangeInfo, list[str], list[str]]
        """

        changes, to_add, to_del = [], [], []

        for argument in arguments:
            if argument in ('-h', '--help'):
                # Manually handle the --help flag
                Assign.display_help()

            if argument[0] == '+':
                to_add.append(argument[1:])
            elif argument[0] == '-':
                to_del.append(argument[1:])
            else:
                changes.append(argument)

        if not to_add and not to_del:
            fail('please specify reviewer(s) to add or delete')

        return fetch_change_list_or_fail(changes), to_add, to_del

    @staticmethod
    def tokenize(idx, change, added, deleted):
        """Token generator for the output

        Yields a stream of tokens: tuple of (Token, string).

        :param idx: index of the change in the list of changes to fetch
        :type idx: int
        :param change: the ChangeInfo corresponding to the change
        :type change: ChangeInfo
        :param added: the list of reviewers added
        :type added: list[ReviewerInfo]
        :param deleted: the list of reviewers deleted
        :type deleted: list[ReviewerInfo]
        :yield: tuple[Token, str]
        """

        if idx:
            yield NEW_LINE

        for token in change.tokenize():
            yield token

        yield NEW_LINE
        yield NEW_LINE

        if not added and not deleted:
            yield Token.Text, (
                '# nothing to do (reviewers list already up-to-date)')
            return

        yield Token.Text, '# Reviewers updated:'

        prefix = (Token.Text, '#     ')

        for reviewer in added:
            yield NEW_LINE
            yield prefix
            yield Token.Review.OK, '+'
            yield Token.Whitespace, ' '

            for token in reviewer.tokenize():
                yield token

        for reviewer in deleted:
            yield NEW_LINE
            yield prefix
            yield Token.Review.KO, '-'
            yield Token.Whitespace, ' '

            for token in reviewer.tokenize():
                yield token

    def run(self, arguments, *args, **kwargs):
        changes, to_add, to_del = self.parse_command_line(arguments)
        assert changes, 'unexpected empty list'

        for idx, change in enumerate(changes):
            added = []
            deleted = []

            # Add reviewers
            for account_id in to_add:
                try:
                    reviewers = Gerrit.add_reviewer(change.uuid, account_id)

                    if reviewers:
                        added.extend(reviewers)

                except PyCRError as why:
                    warn('{}: cannot assign reviewer {}'.format(
                        change.change_id[:9], account_id), why)

            # Delete reviewers
            for account_id in to_del:
                try:
                    review = Gerrit.delete_reviewer(change.uuid, account_id)

                    if review:
                        deleted.append(review.reviewer)

                except PyCRError as why:
                    warn('{}: cannot delete reviewer {}'.format(
                        change.change_id[:9], account_id), why)

            print Formatter.format(self.tokenize(idx, change, added, deleted))
