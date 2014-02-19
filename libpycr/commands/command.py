"""
This module provides the top level Command abstract class.
"""

from abc import ABCMeta, abstractmethod, abstractproperty


# pylint: disable=R0921
# Disable "Abstract class not referenced"
class Command(object):
    """A Command abstract class."""

    __metaclass__ = ABCMeta

    @property
    def name(self):
        """
        The name of the command (ie. to invoke from the command-line).

        RETURNS
            the name as a string
        """
        return self.__class__.__name__.lower()

    @abstractproperty
    def description(self):
        """
        Return a quick description of the command (to be used in the main usage
        message).

        RETURNS
            the description as a string
        """
        pass

    @abstractmethod
    def run(self, arguments, *args, **kwargs):
        """
        The main method that will be used upon command execution.

        PARAMETERS
            arguments: the command-line arguments array

        RAISES
            PyCRError on error
        """
        pass
