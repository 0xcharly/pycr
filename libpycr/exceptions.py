"""Definition of exceptions that can be raised by this library

Every exception from this project inherits from the PyCRError exception.
"""

import os


class PyCRError(Exception):
    """Root exception raised by this module"""

    def __init__(self, message, cause=None):
        self.cause = cause

        if cause is not None:
            message = '{}{}caused by: {}'.format(message, os.linesep,
                                                 str(cause))

        super(PyCRError, self).__init__(message)


class NoSuchChangeError(PyCRError):
    """Exception raised on attempt to manipulate an invalid change"""
    pass


class QueryError(PyCRError):
    """Exception raised on an invalid query"""
    pass


class ConflictError(PyCRError):
    """Exception raised on failed attempt to rebase, submit, ... a revision"""
    pass


class RequestError(PyCRError):
    """Exception raised when catching a requests.exceptions.RequestException"""

    def __init__(self, status_code, response, message, cause=None):
        self.response = response
        self.status_code = status_code
        super(RequestError, self).__init__(message, cause)
