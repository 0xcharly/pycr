"""Compute the version number based on libpycr.VERSION"""

from libpycr.utils.git import get_changeset


def get_version(version=None):
    """Return a PEP 386-compliant version number from VERSION"""

    if version is None:
        from libpycr import VERSION as version
    else:
        assert len(version) == 5
        assert version[3] in ('alpha', 'beta', 'rc', 'final')

    # Now build the two parts of the version number:
    # main = X.Y[.Z]
    # sub = .devN - for pre-alpha releases
    #     | {a|b|c}N - for alpha, beta and rc releases

    parts = 2 if version[2] == 0 else 3
    main = '.'.join(str(x) for x in version[:parts])
    sub = ''

    if version[3] == 'alpha' and version[4] == 0:
        git_changeset = get_changeset()
        if git_changeset:
            sub = '.dev%s' % git_changeset

    elif version[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'c'}
        sub = mapping[version[3]] + str(version[4])

    return str(main + sub)
