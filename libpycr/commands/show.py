"""
Display the code review scores for one or more Gerrit CL.
"""

import argparse

from libpycr.changes import display_change_info, fetch_change_list_or_fail
from libpycr.exceptions import PyCRError
from libpycr.gerrit import Gerrit
from libpycr.pager import Pager
from libpycr.utils.commandline import expect_changes_as_positional
from libpycr.utils.output import Formatter, Token
from libpycr.utils.system import warn


def parse_command_line(arguments):
    """
    Parse the SHOW command command-line arguments.

    PARAMETERS
        arguments: a list of command-line arguments to parse

    RETURNS
        a list of ChangeInfo
    """

    parser = argparse.ArgumentParser(
        description='display code reviews for change(s)')
    expect_changes_as_positional(parser)

    cmdline = parser.parse_args(arguments)

    # Fetch changes details
    return fetch_change_list_or_fail(cmdline.changes)


def main(arguments):
    """
    The entry point for the SHOW command.

    List the reviewers of a change.

    PARAMETERS
        arguments: a list of command-line arguments to parse
    """

    changes = parse_command_line(arguments)
    assert changes, 'unexpected empty list'

    with Pager(command='show'):
        for idx, change in enumerate(changes):
            try:
                reviews = Gerrit.get_reviews(change.uuid)
                patch = Gerrit.get_patch(change.uuid)

            except PyCRError as why:
                warn('%s: cannot list reviewers' % change.change_id[:9], why)
                continue

            if idx:
                print ''

            display_change_info(change)

            for review in reviews:
                print ''
                print '    %s' % Formatter.format([
                    (Token.Text, 'Reviewer: %s' % review.reviewer)])

                for label, score in review.approvals:
                    if score in ('+1', '+2'):
                        token = Token.Review.OK
                    elif score in ('-1', '-2'):
                        token = Token.Review.KO
                    else:
                        token = Token.Review.NONE

                    print '    %s' % Formatter.format([
                        (Token.Text, label),
                        (Token.Text, ': '),
                        (token, score)
                    ])

            print ''
            print Formatter.format_diff(patch)
