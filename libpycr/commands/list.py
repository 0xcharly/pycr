"""
Display the list of changes given the input criterion.
"""

import argparse
import logging

from libpycr.changes import display_change_info
from libpycr.exceptions import NoSuchChangeError, PyCRError
from libpycr.gerrit import Gerrit
from libpycr.utils.system import fail


def parse_command_line(arguments):
    """
    Parse the LIST command command-line arguments.

    PARAMETERS
        arguments: a list of command-line arguments to parse

    RETURNS
        a list of ChangeInfo
    """

    parser = argparse.ArgumentParser(
        description='display list of change(s)')

    parser.add_argument(
        '--owner', default='self', help='the owner of the changes')
    parser.add_argument(
        '--status', default='open', help='the status of the changes')

    cmdline = parser.parse_args(arguments)

    if cmdline.status not in Gerrit.get_all_statuses():
        fail('argument --status: invalid choice "%s" (choose from %s)' %
             (cmdline.status,
              ', '.join(["'%s'" % st for st in Gerrit.get_all_statuses()])))

    # Fetch changes details
    return cmdline.owner, cmdline.status


def main(arguments):
    """
    The entry point for the LIST command.

    List changes.

    PARAMETERS
        arguments: a list of command-line arguments to parse
    """

    log = logging.getLogger(__name__)
    owner, status = parse_command_line(arguments)

    try:
        changes = Gerrit.list_changes(status=status, owner=owner)

    except NoSuchChangeError as why:
        log.debug(str(why))
        return

    except PyCRError as why:
        fail('cannot list changes', why)

    for idx, change in enumerate(changes):
        if idx:
            print ''

        display_change_info(change)
