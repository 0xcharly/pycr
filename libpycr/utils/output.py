"""
This module contains the input / output formatting routines.
"""

import os
import re
import pygments

from libpycr.config import Config

from pygments.formatters import get_all_formatters, get_formatter_by_name
from pygments.lexers.text import DiffLexer
from pygments.style import Style
from pygments.styles import get_style_by_name

from pygments.token import Token as Token


# Newline token
NEW_LINE = (Token.Whitespace, os.linesep)


def update_dict(origin, extras):
    """
    Update the content of ORIGIN with the content of EXTRAS, and return the
    former.

    PARAMETERS
        origin: the dictionary to update
        extras: the dictionary to update ORIGIN with

    RETURNS
        an updated copy of ORIGIN
    """

    final = origin.copy()
    final.update(extras)
    return final


# pylint: disable=R0903
# Disable "Too few public methods"
class OutputStyle(Style):
    """The pygments style to apply to the output."""

    default_style = ''
    native = get_style_by_name('native')
    styles = update_dict(native.styles, {
        Token.Review.OK: native.styles[Token.Generic.Inserted],
        Token.Review.KO: native.styles[Token.Generic.Error],
        Token.Review.NONE: native.styles[Token.Generic.Output],

        Token.Generic.Heading:    '#b4881f',
        Token.Generic.Subheading: '#c0c0c0',

        Token.Text: native.styles[Token.Comment],
        Token.Punctuation: native.styles[Token.Comment]
    })


class Formatter(object):
    """Output formatter."""

    # Heading regex to match a Gerrit diff
    DIFF_HEADING_RE = re.compile('From (?P<commit>[0-9a-f]{8,40}) .*')

    # The formatter name for disabled colored output
    NO_COLOR = 'null'

    # The formatter to use
    formatter = None

    @staticmethod
    def get_all():
        """
        List all available formatters.

        RETURNS
            a list of string containing the label of all formaters
        """

        return get_all_formatters()

    @classmethod
    def set_formatter(cls, formatter_name='terminal256'):
        """
        Set the formatter to use for the output.

        PARAMETERS
            formatter_name: the name of the Pygments formatter
        """

        Config.set('core.formatter', formatter_name)

    @classmethod
    def __initialize(cls):
        """
        Initialize the object if needed.
        """

        if cls.formatter is None:
            name = Config.get('core.color', Formatter.NO_COLOR)

            if name == 'auto':
                name = 'terminal256'

            cls.formatter = get_formatter_by_name(name, style=OutputStyle,
                                                  encoding='utf-8')

    @classmethod
    def format(cls, tokens):
        """
        Format the given list of tokens.

        PARAMETERS
            tokens: the input list of token to format

        RETURNS
            the formatted string
        """

        cls.__initialize()
        return pygments.format(tokens, cls.formatter)

    @classmethod
    def tokenize_diff(cls, diff):
        """
        Token generator for a patch string

        PARAMETERS
            diff: the patch to format

        RETURNS
            a stream of tokens: tuple of (Token, string)
        """

        heading = diff.splitlines()[0]
        match = Formatter.DIFF_HEADING_RE.match(heading)
        diff = diff[len(heading):]

        if match:
            yield Token.Generic.Heading, 'commit %s' % match.group('commit')
            yield NEW_LINE

        for token in pygments.lex(diff, DiffLexer(encoding='utf-8')):
            yield token
