"""Review a change"""

import argparse
import logging
import os

from libpycr.editor import raw_input_editor, strip_comments
from libpycr.exceptions import NoSuchChangeError, PyCRError
from libpycr.gerrit.client import Gerrit
from libpycr.meta import GitClBuiltin
from libpycr.utils.output import Formatter, NEW_LINE
from libpycr.utils.system import ask, fail


class Review(GitClBuiltin):
    """Implement the REVIEW command"""

    log = logging.getLogger(__name__)

    @property
    def description(self):
        return 'code-review a change'

    @staticmethod
    def parse_command_line(arguments):
        """Parse the SUBMIT command command-line arguments

        Returns a tuple with a change_id and a revision_id.

        :param arguments: a list of command-line arguments to parse
        :type arguments: list[str]
        :rtype: str, str
        """

        parser = argparse.ArgumentParser(description='Code-review a change')
        parser.add_argument(
            'change_id', metavar='CL',
            help='Gerrit Code Review CL / CL range / Change-Id')
        parser.add_argument(
            'score', help='the score of the review', default=None,
            choices=Gerrit.SCORES, nargs='?')
        parser.add_argument('-m', '--message', help='the review comment')

        cmdline = parser.parse_args(arguments)

        return cmdline.change_id, cmdline.score, cmdline.message

    @staticmethod
    def tokenize(change, review):
        """Token generator for the output

        Yields a stream of tokens: tuple of (Token, string).

        :param change: the change
        :type change: ChangeInfo
        :param review: the review
        :type review: ReviewInfo
        :yield: tuple[Token, str]
        """

        for token in change.tokenize():
            yield token

        yield NEW_LINE
        yield NEW_LINE

        for token in review.tokenize():
            yield token

    def run(self, arguments, *args, **kwargs):
        change_id, score, message = Review.parse_command_line(arguments)

        try:
            change = Gerrit.get_change(change_id)

            if message is None:
                initial_content = [
                    '',
                    ('# Please enter the comment message for your review. '
                     'Lines starting'),
                    "# with '#' will be ignored.",
                    '#'
                ]
                initial_content.extend(
                    ['# %s' % line for line in change.raw_str().splitlines()])
                initial_content.append('#')

                message = raw_input_editor(os.linesep.join(initial_content))
                message = strip_comments(message)

            if score is None:
                score = ask('Please enter your review score', Gerrit.SCORES)

            review = Gerrit.set_review(score, message, change.uuid)

        except NoSuchChangeError as why:
            self.log.debug(str(why))
            fail('invalid change')

        except PyCRError as why:
            fail('cannot post review', why)

        print Formatter.format(Review.tokenize(change, review))
