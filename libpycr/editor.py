"""
This module provides convenient use of EDITOR.
"""

import os
import subprocess
import tempfile

from libpycr.config import Config


def get_editor():
    """
    Return the user's editor, or vi if not defined.

    RETURNS
        the prefered editor
    """

    return os.environ.get('EDITOR') or os.environ.get('VISUAL') or 'vi'


def strip_comments(data, line_comment='#'):
    """
    Strip comments from the input string.

    PARAMETERS
        data: input string
        line_comment: the line comment delimiter

    RETURNS
        the input string striped from comments
    """

    lines = []

    for line in data.splitlines():
        idx = line.find(line_comment)
        lines.append((line if idx == -1 else line[:idx]).strip())

    return '\n'.join(lines).strip()


def raw_input_editor(default=None):
    """
    Like the built-in raw_input(), except that it uses a visual
    text editor for ease of editing.

    PARAMETERS
        editor: the editor to use
        default: the initital content of the editor

    RETURNS
        the final content after edition
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
