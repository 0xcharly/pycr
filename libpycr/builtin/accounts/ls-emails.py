"""List emails associated with one's account"""

# pylint: disable=invalid-name

import argparse
import logging

from libpycr.exceptions import PyCRError
from libpycr.gerrit.client import Gerrit
from libpycr.meta import GerritAccountBuiltin
from libpycr.pager import Pager
from libpycr.utils.commandline import expect_account_as_positional
from libpycr.utils.system import fail

from prettytable import PrettyTable


class LsEmails(GerritAccountBuiltin):
    """Implement the LS-EMAILS command"""

    # Logger for this command
    log = logging.getLogger(__name__)

    @property
    def name(self):
        return 'ls-emails'

    @property
    def description(self):
        return 'list email(s)'

    @staticmethod
    def parse_command_line(arguments):
        """Parse the LS-EMAILS command command-line arguments

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: list[ChangeInfo]
        """

        parser = argparse.ArgumentParser(description='List account email(s)')
        expect_account_as_positional(parser)

        cmdline = parser.parse_args(arguments)

        # fetch changes details
        return cmdline.account

    def run(self, arguments, *args, **kwargs):
        account_id = LsEmails.parse_command_line(arguments)

        try:
            account = Gerrit.get_account(account_id or 'self')
            emails = Gerrit.get_emails(account_id or 'self')

        except PyCRError as why:
            fail('cannot list account emails', why)

        table = PrettyTable(['Email', 'Preferred', 'Confirmed'])
        table.align = 'l'

        for email in emails:
            table.add_row([email.email,
                           u'\u2713' if email.preferred else '',
                           'No' if email.pending_confirmation else 'Yes'])

        with Pager(command=self.name):
            print 'Account: {}'.format(account.username)
            if emails:
                print table
            else:
                print 'No email address'
