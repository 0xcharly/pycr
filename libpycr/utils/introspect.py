"""This module provides introspection helpers"""


def get_all_subclasses(klass):
    """Return all subclasses of a class

    Use Python introspection to list all subclasses of the given class.
    This function do not stop to the direct children, but walk the whole
    inheritance tree.

    :param klass: the root class to use for introspection
    :type klass: T
    :rtype: tuple(T)
    """

    subclasses = set()
    queue = [klass]

    while queue:
        parent = queue.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                queue.append(child)

    return tuple(subclasses)
