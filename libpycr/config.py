"""
This module manipulates the configuration files for this project.
"""

import os

from ConfigParser import ParsingError, SafeConfigParser

from libpycr.http import RequestFactory
from libpycr.utils.system import fail, warn, reverse_find_file


# pylint: disable=R0903
# Disable "Too few public methods"
class Config(object):
    """Script configuration."""

    SECTION = 'gerrit'

    FILENAME = '.gitreview'
    GLOBAL = os.path.expanduser('~/%s' % FILENAME)

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

        if not parser.has_section(Config.SECTION):
            fail('missing section [%s]' % Config.SECTION)

        # Configure the HTTP request engine
        if parser.has_option(Config.SECTION, 'host'):
            RequestFactory.set_host(parser.get(Config.SECTION, 'host'))

        if parser.has_option(Config.SECTION, 'username'):
            username = parser.get(Config.SECTION, 'username')

            if parser.has_option(Config.SECTION, 'password'):
                password = parser.get(Config.SECTION, 'password')
            else:
                password = None

            RequestFactory.set_auth_token(username, password)

    @staticmethod
    def load_all():
        """
        Load all configuration files available.
        """

        Config.load(Config.GLOBAL, quiet=True)

        local = reverse_find_file(Config.FILENAME, ignores=[Config.GLOBAL])

        if local is not None:
            Config.load(local)
