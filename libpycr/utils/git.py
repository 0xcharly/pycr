"""
This modules contains the low level routine to interact with an instance of a
Git repository.
"""

import datetime
import os
import subprocess


def get_changeset():
    """Return a numeric identifier of the latest git changeset.

    The result is the UTC timestamp of the changeset in YYYYMMDDHHMMSS format.
    This value isn't guaranteed to be unique, but collisions are very unlikely,
    so it's sufficient for generating the development version numbers.

    RETURNS
        a numeric identifier of the latest git changeset as a string
    """

    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    git_log = subprocess.Popen(
        'git log --pretty=format:%ct --quiet -1 HEAD',
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        shell=True, cwd=repo_dir, universal_newlines=True)
    output, _ = git_log.communicate()

    try:
        timestamp = datetime.datetime.utcfromtimestamp(int(output))

    except ValueError:
        return None

    return timestamp.strftime('%Y%m%d%H%M%S')
