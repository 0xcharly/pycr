"""
This module provides introspection helpers.
"""


def get_all_subclasses(klass):
    """
    Use Python introspection to list all subclasses of the given class.
    This function do not stop to the direct children, but walk the whole
    inheritance tree.

    PARAMETERS
        klass: the root class to use for introspection

    RETURNS
        a set of subclasses
    """

    subclasses = set()
    queue = [klass]

    while queue:
        parent = queue.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                queue.append(child)

    return subclasses
