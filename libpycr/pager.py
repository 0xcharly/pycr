"""
This module provides convenient use of PAGER.
"""

import os
import sys
from subprocess import Popen, PIPE

from libpycr.config import Config


def get_pager():
    """
    Return the user's pager, or less if not defined.

    RETUNRS
        the prefered pager
    """

    return os.environ.get('PAGER') or 'less'


# pylint: disable=R0903
# Disable "Too few public methods" (for all above classes)
class Pager(object):
    """Display CONTENT in a pager, or on the standard output stream if pager is
    disabled.
    """

    def __init__(self, command):
        self._pager_proc = None
        self.command = command

    def __enter__(self):
        pager = Config.get('core.pager', get_pager())
        pager = Config.get('pager.%s' % self.command, pager)

        if pager:
            env = os.environ.copy()
            if 'LESS' not in env:
                env['LESS'] = 'FRSX'
            if 'LV' not in env:
                env['LV'] = '-c'
            self._pager_proc = Popen([pager], stdin=PIPE, env=env)
            sys.stdout = self._pager_proc.stdin

    def __exit__(self, typ, value, traceback):
        if self._pager_proc:
            sys.stdout = sys.__stdout__
            self._pager_proc.stdin.close()
            self._pager_proc.wait()
            self._pager_proc = None
