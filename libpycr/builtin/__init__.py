"""Contains the CL tool builtins."""


def __find_all_modules():
    """Find all sub-modules.

    Read the current directory and generate the list of all modules present
    it. Use this function as a generator.
    """

    import os
    this, _ = os.path.splitext(os.path.basename(__file__))

    for fname in os.listdir(os.path.dirname(__file__)):
        base, ext = os.path.splitext(fname)
        if ext != '.pyc' and not base.startswith('.') and base != this:
            yield base

__all__ = list(__find_all_modules())
