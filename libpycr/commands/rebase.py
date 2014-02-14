"""
Rebase a revision.
"""

import argparse
import logging

from libpycr.exceptions import NoSuchChangeError, PyCRError
from libpycr.gerrit import Gerrit
from libpycr.utils.output import Formatter, Token, NEW_LINE
from libpycr.utils.system import fail


def parse_command_line(arguments):
    """
    Parse the REBASE command command-line arguments.

    PARAMETERS
        arguments: a list of command-line arguments to parse

    RETURNS
        a tuple with a change_id and a revision_id
    """

    parser = argparse.ArgumentParser(description='rebase a revision')

    parser.add_argument(
        '--revision', dest='revision_id', default='current',
        help='the revision to rebase (default to current)')
    parser.add_argument('change_id', metavar='CL', help='the change to rebase')

    cmdline = parser.parse_args(arguments)

    # Fetch changes details
    return cmdline.change_id, cmdline.revision_id


def tokenize(change):
    """
    Token generator for the output.

    PARAMETERS
        change: the ChangeInfo corresponding to the change

    RETURNS
        a stream of tokens: tuple of (Token, string)
    """

    for token in change.tokenize():
        yield token

    yield NEW_LINE
    yield Token.Generic.Heading, 'commit: %s' % change.current_revision


def main(arguments):
    """
    The entry point for the REBASE command.

    Rebase revision.

    PARAMETERS
        arguments: a list of command-line arguments to parse
    """

    log = logging.getLogger(__name__)
    change_id, revision_id = parse_command_line(arguments)

    try:
        change = Gerrit.rebase(change_id, revision_id)

    except NoSuchChangeError as why:
        log.debug(str(why))
        fail('invalid change or revision')

    except PyCRError as why:
        fail('cannot rebase', why)

    print Formatter.format(tokenize(change))
