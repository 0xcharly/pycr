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

    editor = Config('core.editor', get_editor())

    with tempfile.NamedTemporaryFile(mode='r+', delete=True) as tmpfile:
        if default:
            tmpfile.write(default)
            tmpfile.flush()

        subprocess.check_call([editor or get_editor(), tmpfile.name])
        tmpfile.seek(0)

        return tmpfile.read().strip()
