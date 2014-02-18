"""
Rebase a change.
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

    parser = argparse.ArgumentParser(description='Rebase a change.')
    parser.add_argument('change_id', metavar='CL',
                        help='Gerrit Code Review CL / CL range / Change-Id')

    cmdline = parser.parse_args(arguments)

    return cmdline.change_id


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
    yield NEW_LINE

    yield Token.Text, 'Change successfully rebased (new revision: '
    yield Token.Keyword, change.current_revision[:8]
    yield Token.Text, ')'


def main(arguments):
    """
    The entry point for the REBASE command.

    Rebase revision.

    PARAMETERS
        arguments: a list of command-line arguments to parse
    """

    log = logging.getLogger(__name__)
    change_id = parse_command_line(arguments)

    try:
        change = Gerrit.rebase(change_id)

    except NoSuchChangeError as why:
        log.debug(str(why))
        fail('invalid change')

    except PyCRError as why:
        fail('cannot rebase', why)

    print Formatter.format(tokenize(change))
