"""
This module contains the low level, operating system routines used for file
input / output.
"""

import os
import sys


def format_message(message, prefix=None, why=None):
    """
    Format a message, along with the prefix and exception message if provided.

    PARAMETERS
        message: the message to print
        prefix: optional prefix to the message
        why: optional exception to display. Defaults to None

    RETURNS
        the formatted message as a string
    """

    buf = []

    if prefix is not None:
        buf.append(prefix)

    buf.append(message)

    if why is not None:
        buf.append(str(why))

    return ': '.join(buf)


def info(message):
    """
    Print an informative message. Use the standard output stream.

    PARAMETERS
        message: the message to print
    """

    print format_message(message)


def warn(message, why=None):
    """
    Print a warning message, along with the exception message if provided.
    Use the error output stream.

    PARAMETERS
        message: the message to print
        why: optional exception to display. Defaults to None
    """

    print >> sys.stderr, format_message(message, prefix='warning', why=why)


def fail(message, why=None):
    """
    Print an error message, along with the exception message if provided.
    Use the error output stream. Exit the program with error code 1.

    PARAMETERS
        message: the message to print
        why: optional exception to display. Defaults to None
    """

    sys.exit(format_message(message, prefix='error', why=why))


def confirm(question):
    """
    Request user input to the given question. Expect a yes/no answer.

    PARAMETERS
        question: question to ask the user

    RETURNS
        True if the answer is YES, False otherwise
    """

    print question
    answer = raw_input("Type 'yes' to confirm, other to cancel: ").lower()

    return answer in ('y', 'yes')


def ask(question, choices=None):
    """
    Request user input to the given question. If CHOICES is not None, display
    the list of choices and expect an index.

    PARAMETERS
        question: question to ask the user
        choices: if not None, the allowable values for the answer

    RETURNS
        True if the answer is YES, False otherwise
    """

    if choices is None:
        return raw_input('%s: ' % question)

    while True:
        answer = raw_input('%s: ' % question)

        if answer in choices:
            break

        print >> sys.stderr, ('Invalid input (expected %s)' %
                              ', '.join(choices))

    return answer


def reverse_find_file(filename, origin=os.getcwd(), ignores=None):
    """
    Look for a given filename in the current directory. Try the parent
    directories until found of file-system root reached.

    PARAMETERS
        filename: the file name as a string
        origin: the origin directory for the search
        ignores: an optional list of files to ignore

    RETURNS
        the path to the file as a string, or None if not found
    """

    directory = origin
    inspected = None

    ignore_list = [] if ignores is None else ignores

    while directory != inspected:
        lookup = os.path.join(directory, filename)

        if os.path.isfile(lookup) and lookup not in ignore_list:
            break

        inspected = directory
        directory = os.path.dirname(directory)

    if directory == inspected:
        return None

    assert lookup is not None, 'internal error'
    return lookup
