"""
This module contains the various exceptions that can be raised during the
execution of the many commands.

Every exception from this project inherits from the PyCRError exception.
"""

import os


class PyCRError(Exception):
    """Root exception raised by this module."""

    def __init__(self, message, cause=None):
        self.cause = cause

        if cause is not None:
            message = '%s%scaused by: %s' % (message, os.linesep, str(cause))

        super(PyCRError, self).__init__(message)


class NoSuchChangeError(PyCRError):
    """Exception raised on attempt to manipulate an invalid change."""
    pass


class RequestError(PyCRError):
    """Exception raised when catching a requests.exceptions.RequestException.
    """

    def __init__(self, status_code, message, cause=None):
        self.status_code = status_code
        super(RequestError, self).__init__(message, cause)
