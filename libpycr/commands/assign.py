"""
Assign one or more reviewers to one or more Gerrit CL.
"""

import os
import sys

from libpycr.changes import display_change_info, fetch_change_list_or_fail
from libpycr.exceptions import PyCRError
from libpycr.gerrit import Gerrit
from libpycr.utils.output import Formatter, Token
from libpycr.utils.system import fail, warn


def display_help():
    """
    Display the help for this command and exit.

    We have to forge our own help output because we do not use the argparse
    module to parse the command-line arguments.
    """

    buf = ['usage: cl [-h] CL [CL ...] [+REVIEWER [+REVIEWER ...]]']
    buf.append('                           [-REVIEWER [-REVIEWER ...]]')
    buf.append('')
    buf.append('add/delete reviewer(s) to change(s)')
    buf.append('')
    buf.append('positional arguments:')
    buf.append('  CL             Gerrit Code Review CL / CL range / Change-Id')
    buf.append('  +REVIEWER      add REVIEWER to the change')
    buf.append('  -REVIEWER      delete REVIEWER from the change')
    buf.append('')
    buf.append('optional arguments:')
    buf.append('  -h, --help     show this help message and exit')

    print os.linesep.join(buf)
    sys.exit()


def parse_command_line(arguments):
    """
    Parse the SHOW command command-line arguments.

    PARAMETERS
        arguments: a list of command-line arguments to parse

    RETURNS
        a tuple containing three lists:
            - the list of ChangeInfo
            - the list of reviewers to add
            - the list of reviewers to delete
    """

    changes, to_add, to_del = [], [], []

    for argument in arguments:
        if argument in ('-h', '--help'):
            # Manually handle the --help flag
            display_help()

        if argument[0] == '+':
            to_add.append(argument[1:])
        elif argument[0] == '-':
            to_del.append(argument[1:])
        else:
            changes.append(argument)

    if not to_add and not to_del:
        fail('please specify reviewer(s) to add or delete')

    return fetch_change_list_or_fail(changes), to_add, to_del


def main(arguments):
    """
    The entry point for the ASSIGN command.

    Add or delete one or several reviewers to one or more change.

    PARAMETERS
        arguments: a list of command-line arguments to parse
    """

    changes, to_add, to_del = parse_command_line(arguments)
    assert changes, 'unexpected empty list'

    for idx, change in enumerate(changes):
        added = []
        deleted = []

        if idx:
            print ''

        # Add reviewers
        for account_id in to_add:
            try:
                reviewers = Gerrit.add_reviewer(change.uuid, account_id)

                if reviewers:
                    added.extend(reviewers)

            except PyCRError as why:
                warn('%s: cannot assign reviewer %s' %
                     (change.change_id[:9], account_id), why)

        # Delete reviewers
        for account_id in to_del:
            try:
                review = Gerrit.delete_reviewer(change.uuid, account_id)

                if review:
                    deleted.append(review.reviewer)

            except PyCRError as why:
                warn('%s: cannot delete reviewer %s' %
                     (change.change_id[:9], account_id), why)

        display_change_info(change)
        print ''

        if not added and not deleted:
            print '# nothing to do (reviewers list already up-to-date)'
            continue

        print '# Reviewers updated:'

        prefix = (Token.Whitespace, '#     ')
        for reviewer in added:
            print Formatter.format([
                prefix,
                (Token.Review.OK, '+'),
                (Token.Text, ' %s' % reviewer)
            ])

        for reviewer in deleted:
            print Formatter.format([
                prefix,
                (Token.Review.KO, '-'),
                (Token.Text, ' %s' % reviewer)
            ])
