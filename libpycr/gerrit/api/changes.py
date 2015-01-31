"""Change related REST endpoints"""

from libpycr.http import RequestFactory


def base_query():
    """Return an URL to Gerrit

    :rtype: str
    """

    return '{}/changes/'.format(RequestFactory.get_remote_base_url())


def accounts_query():
    """Return an URL to Gerrit

    :rtype: str
    """

    return '{}/accounts/'.format(RequestFactory.get_remote_base_url())


def changes(change_id):
    """Return an URL to Gerrit for the given change

    :param change_id: any identification number for the change (UUID,
        Change-Id, or legacy numeric change ID)
    :type change_id: str
    :rtype: str
    """

    return base_query() + change_id


def detailed_changes(change_id):
    """Return an URL to Gerrit for the given change

    :param change_id: any identification number for the change (UUID,
        Change-Id, or legacy numeric change ID)
    :type change_id: str
    :rtype: str
    """

    return '{}/detail'.format(changes(change_id))


def revisions(change_id, revision_id):
    """Return an URL to Gerrit

    This URL allows queries to a specific reviesion of the given change.

    :param change_id: any identification number for the change (UUID,
        Change-Id, or legacy numeric change ID)
    :type change_id: str
    :param revision_id: identifier that uniquely identifies one revision of
        a change (current, a commit ID (SHA1) or abbreviated commit ID, or
        a legacy numeric patch number)
    :type revision_id: str
    :rtype: str
    """

    return '{}/revisions/{}'.format(changes(change_id), revision_id)


def patch(change_id, revision_id):
    """Return an URL to Gerrit

    This URL allows queries for the patch of the given change.

    :param change_id: any identification number for the change (UUID,
        Change-Id, or legacy numeric change ID)
    :type change_id: str
    :param revision_id: identifier that uniquely identifies one revision of
        a change (current, a commit ID (SHA1) or abbreviated commit ID, or
        a legacy numeric patch number)
    :type revision_id: str
    :rtype: str
    """

    return '{}/patch'.format(revisions(change_id, revision_id))


def review(change_id, revision_id):
    """Return an URL to Gerrit

    This URL allows queries to set a review for the given revision of a
    change.

    :param change_id: any identification number for the change (UUID,
        Change-Id, or legacy numeric change ID)
    :type change_id: str
    :param revision_id: identifier that uniquely identifies one revision of
        a change (current, a commit ID (SHA1) or abbreviated commit ID, or
        a legacy numeric patch number)
    :type revision_id: str
    :rtype: str
    """

    return '{}/review'.format(revisions(change_id, revision_id))


def rebase(change_id):
    """Return an URL to Gerrit

    This URL allows queries to rebase the given change.

    :param change_id: any identification number for the change (UUID,
        Change-Id, or legacy numeric change ID)
    :type change_id: str
    :rtype: str
    """

    return '{}/rebase'.format(changes(change_id))


def submit(change_id):
    """Return an URL to Gerrit

    This URL allows queries to submit the given change.

    :param change_id: any identification number for the change (UUID,
        Change-Id, or legacy numeric change ID)
    :type change_id: str
    :rtype: str
    """

    return '{}/submit'.format(changes(change_id))


def reviewers(change_id):
    """Return an URL to Gerrit

    This URL allows queries for reviewers of the given change.

    :param change_id: any identification number for the change (UUID,
        Change-Id, or legacy numeric change ID)
    :type change_id: str
    :rtype: str
    """

    return '{}/reviewers'.format(changes(change_id))


def reviewer(change_id, account_id):
    """Return an URL to Gerrit

    This URL allows queries for reviewers of the given change.

    :param change_id: any identification number for the change (UUID,
        Change-Id, or legacy numeric change ID)
    :type change_id: str
    :param account_id: any identification string for an account (name,
        username, email)
    :type account_id: str
    :rtype: str
    """

    return '{}/{}'.format(reviewers(change_id), account_id)


# pylint: disable=redefined-outer-name
# Allow re-use of 'reviewer' name as keyword argument.


def search_query_attr(status=None, owner=None, reviewer=None, watched=None):
    """Create a search query compatible with Gerrit Code Review queries

    :param status: the status of changes
    :type status: str
    :param owner: the owner of changes
    :type owner: str
    :param reviewer: the reviewer of changes
    :type reviewer: str
    :param watched: whether the change should be in the watched list or not
    :type watched: str
    :rtype: str
    """

    buf = []

    if status is not None:
        buf.append('status:%s' % status)

    if owner is not None:
        buf.append('owner:%s' % owner)

    if reviewer is not None:
        buf.append('reviewer:%s' % reviewer)

    if watched is not None:
        buf.append('is:watched')

    return '+'.join(buf)


def search_query(status=None, owner=None, reviewer=None, watched=None):
    """Return an URL to Gerrit

    This URL contains the query to perform.

    :param status: the status of changes
    :type status: str
    :param owner: the owner of changes
    :type owner: str
    :param reviewer: the reviewer of changes
    :type reviewer: str
    :rtype: str
    """

    # NOTE: We can't use the params= parameter of the requests.get
    # method because this would encode the query string and prevent
    # Gerrit from parsing it

    return '{}?q={}'.format(
        base_query(), search_query_attr(status=status, owner=owner,
                                        reviewer=reviewer, watched=watched))
