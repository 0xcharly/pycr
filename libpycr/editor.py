"""This module provides convenient use of EDITOR"""

import os
import subprocess
import tempfile

from libpycr.config import Config


def get_editor():
    """Return the user's editor, or vi if not defined

    :rtype: str
    """

    return os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'vi'


def strip_comments(data, line_comment='#'):
    """Strip comments from the input string and return the result

    :param data: multiline text to strip comments from
    :type data: str
    :param line_comment: the line comment delimiter
    :type line_comment: str
    :rtype: str
    """

    return '\n'.join([l for l in data.splitlines()
                      if l[0] != line_comment]).strip()


def raw_input_editor(default=None):
    """Request user input by firing an editor

    Like the built-in raw_input(), except that it uses a visual text editor for
    ease of editing.

    :param editor: the editor to use
    :type editor: str
    :param default: the initital content of the editor
    :type default: str | None
    """

    editor = Config.get('core.editor', get_editor())

    with tempfile.NamedTemporaryFile(mode='r+', delete=False) as tmpfile:
        if default:
            tmpfile.write(default)
            tmpfile.flush()

        # NOTE: We need to close then re-open the file after edition to ensure
        # that buffers are correctly emptied on all platforms.
        tmpfile.close()

        subprocess.check_call([editor, tmpfile.name])

        with open(tmpfile.name) as comment_file:
            comment = comment_file.read().strip()

        os.unlink(tmpfile.name)

    return comment
