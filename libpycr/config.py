"""
This module manipulates the configuration files for this project.
"""

import os
import sys

from ConfigParser import ParsingError, SafeConfigParser

from libpycr.utils.system import fail, warn, reverse_find_file


# pylint: disable=R0903
# Disable "Too few public methods"
class Config(dict):
    """Script configuration."""

    # The configuration file name
    FILENAME = 'gitreview'

    # Windows:   C:\etc\gitreview
    # Otherwise: /etc/gitreview
    SYSTEM = os.path.join(
        os.path.splitdrive(sys.executable)[0] or '/', 'etc', FILENAME)

    # $HOME/.gitreview
    GLOBAL = os.path.expanduser('~/.%s' % FILENAME)

    # Dictionary of configuration keys
    __config = {}

    @classmethod
    def load(cls, filename, quiet=False):
        """
        Parse a configuration file and extract this script's configuration.

        PARAMETERS
            filename: the path to the config file
        """

        if not os.path.isfile(filename):
            if not quiet:
                warn('%s: No such file or directory' % filename)

            return

        parser = SafeConfigParser()

        try:
            with open(filename, 'r') as config:
                parser.readfp(config, filename)
        except ParsingError as why:
            fail('failed to parse configuration: %s' % config, why)

        cls._store_config(parser)

    @staticmethod
    def load_all():
        """
        Load all configuration files available.
        """

        Config.load(Config.SYSTEM, quiet=True)
        Config.load(Config.GLOBAL, quiet=True)

        local = reverse_find_file('.%s' % Config.FILENAME,
                                  ignores=[Config.GLOBAL])

        if local is not None:
            Config.load(local)

    @classmethod
    def get(cls, key, default=None):
        """
        Return the configuration value associated with KEY, or DEFAULT
        otherwise.

        PARAMETERS
            key: the configuration key
            default: the default value to return if key is not if the
                configuration

        RETURNS
            the value associated with KEY, or DEFAULT
        """

        return cls.__config.get(key, default)

    @classmethod
    def _store_config(cls, config):
        """
        Store each element of the configuration file.

        If the element already exists, this method will override it.

        PARAMETERS
            config: ConfigParser.SafeConfigParser
        """

        for section in config.sections():
            for option, value in config.items(section):
                cls.__config['%s.%s' % (section, option)] = value

    @classmethod
    def set(cls, key, value):
        """
        Create or override an entry in the configuration dictionary.

        PARAMETERS
            key: the key to insert or override
            value: the value to associate with the key
        """

        cls.__config[key] = value
