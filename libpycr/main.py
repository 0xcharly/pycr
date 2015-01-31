"""Generic main function"""

import os
import sys

from libpycr.commandline import parse_command_line
from libpycr.config import Config
from libpycr.exceptions import PyCRError
from libpycr.utils.system import format_message


def builtin_main(builtin_type):
    """Generic main function

    :param builtin_type: the type of Builtin to look for
    :type builtin_type: Builtin
    """

    try:
        # Load various input configurations
        Config.load_all()

        # Fetch the result of the command-line parsing
        command, arguments = parse_command_line(builtin_type)

        # Execute the requested command
        command.run(arguments)

    except PyCRError as why:
        sys.exit(format_message(str(why), prefix='fatal'))

    except KeyboardInterrupt:
        sys.exit(os.linesep + 'Interruption caught...')

    sys.exit()
