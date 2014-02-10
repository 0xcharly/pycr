"""
This module manipulates the configuration files for this project.
"""

import os
import sys

from ConfigParser import ParsingError, SafeConfigParser

from libpycr.http import RequestFactory
from libpycr.utils.output import Formatter
from libpycr.utils.system import fail, warn, reverse_find_file


# pylint: disable=R0903
# Disable "Too few public methods"
class Config(object):
    """Script configuration."""

    # The configuration file name
    FILENAME = 'gitreview'

    # Windows:   C:\etc\gitreview
    # Otherwise: /etc/gitreview
    SYSTEM = os.path.join(
        os.path.splitdrive(sys.executable)[0] or '/', 'etc', FILENAME)

    # $HOME/.gitreview
    GLOBAL = os.path.expanduser('~/.%s' % FILENAME)

    # Gerrit Code Review remote server host
    host = None

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

        cls._read_core_config(parser)
        cls._read_gerrit_config(parser)

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
    def _read_gerrit_config(cls, config):
        """
        Read the configuration for the [gerrit] section.

        PARAMETERS
            config: ConfigParser.SafeConfigParser
        """

        section = 'gerrit'

        if not config.has_section(section):
            # This section is not mandatory for a given config file
            return

        # Configure the HTTP request engine
        if config.has_option(section, 'host'):
            RequestFactory.set_host(config.get(section, 'host'))

        if config.has_option(section, 'username'):
            username = config.get(section, 'username')

            if config.has_option(section, 'password'):
                password = config.get(section, 'password')
            else:
                password = None

            RequestFactory.set_auth_token(username, password)

    @classmethod
    def _read_core_config(cls, config):
        """
        Read the configuration for the [cl] section.

        PARAMETERS
            config: ConfigParser.SafeConfigParser
        """

        section = 'core'

        if not config.has_section(section):
            # This section is not mandatory
            return

        if config.has_option(section, 'color'):
            color = config.get(section, 'color')

            if color == 'auto':
                # Use the default style
                Formatter.set_formatter()
            else:
                # Attempt to use the user-declared style
                Formatter.set_formatter(color)
