"""Meta classes declaration"""

from abc import ABCMeta, abstractmethod, abstractproperty


# pylint: disable=R0921
# Disable "Abstract class not referenced"
class Builtin(object):
    """A Builtin abstract class"""

    __metaclass__ = ABCMeta

    @property
    def name(self):
        """The name of the command (ie. to invoke from the command-line)

        :rtype: str
        """
        return self.__class__.__name__.lower()

    @abstractproperty
    def description(self):
        """Return a quick description of the command

        This is used in the main usage message.

        :rtype: str
        """
        pass

    @abstractmethod
    def run(self, arguments, *args, **kwargs):
        """The main method that will be used upon command execution

        :param arguments: the command-line arguments array
        :type arguments: list[str]
        :raise: PyCRError on error
        """
        pass
