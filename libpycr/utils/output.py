"""
This module contains the input / output formatting routines.
"""

import pygments

from pygments.formatters import get_all_formatters, get_formatter_by_name
from pygments.style import Style
from pygments.styles import get_style_by_name

from pygments.token import Token as Token


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
        Token.Review.OK: '#729519',
        Token.Review.KO: native.styles[Token.Generic.Error],
        Token.Review.NONE: native.styles[Token.Comment],

        Token.Generic.Heading: '#b4881f'
    })


class Formatter(object):
    """Output formatter."""

    # The formatter name for disabled colored output
    NO_COLOR = 'null'

    # The formatter to use; defaults to "null" (no color)
    formatter = get_formatter_by_name(NO_COLOR, style=OutputStyle)

    @staticmethod
    def get_all():
        """
        List all available formatters.

        RETURNS
            a list of string containing the label of all formaters
        """

        return get_all_formatters()

    @classmethod
    def set_formatter(cls, formatter_name='terminal256', style=OutputStyle):
        """
        Set the formatter to use for the output.

        PARAMETERS
            formatter_name: the name of the Pygments formatter
            style: a dictionary of style to use for output
        """

        cls.formatter = get_formatter_by_name(formatter_name, style=style)

    @classmethod
    def format(cls, tokens):
        """
        Format the given list of tokens.

        PARAMETERS
            tokens: the input list of token to format

        RETURNS
            the formatted string
        """

        return pygments.format(tokens, cls.formatter)
