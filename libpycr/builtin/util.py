"""Utility functions"""


def find_all(builtin_module_init):
    """Find all builtin implemented in sub-modules

    Read the given directory and generate the list of all modules present
    it. Use this function as a generator.
    """

    import os

    for fname in os.listdir(os.path.dirname(builtin_module_init)):
        base, ext = os.path.splitext(fname)
        if ext != '.pyc' and not base.startswith('.') and base != '__init__':
            yield base
