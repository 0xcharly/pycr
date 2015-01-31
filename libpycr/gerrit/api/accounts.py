"""Account related REST endpoints"""

from libpycr.http import RequestFactory


def base_query():
    """Return an URL to Gerrit

    :rtype: str
    """

    return '{}/accounts/'.format(RequestFactory.get_remote_base_url())


def account(account_id):
    """Return an URL to Gerrit for an account

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return base_query() + account_id


def name(account_id):
    """Return an URL to Gerrit for an account name

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return '{}/name'.format(account(account_id))


def username(account_id):
    """Return an URL to Gerrit for an account username

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return '{}/username'.format(account(account_id))


def active(account_id):
    """Return an URL to Gerrit

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return '{}/active'.format(account(account_id))


def http_password(account_id):
    """Return an URL to Gerrit

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return '{}/password.http'.format(account(account_id))


def avatar(account_id):
    """Return an URL to Gerrit for an account avatar

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return '{}/avatar'.format(account(account_id))


def avatar_change_url(account_id):
    """Return an URL to Gerrit for an account avatar change URL

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return '{}/avatar.change.url'.format(account(account_id))


def diff_preferences(account_id):
    """Return an URL to Gerrit for an account diff preferences

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return '{}/preferences.diff'.format(account(account_id))


def starred_changes(account_id):
    """Return an URL to Gerrit for an account starred changes

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return '{}/starred.changes'.format(account(account_id))


def starred_change(account_id, change_id):
    """Return an URL to Gerrit for an account starred change

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :param change_id: any identification number for the change (UUID,
        Change-Id, or legacy numeric change ID)
    :type change_id: str
    :rtype: str
    """

    return '{}/{}'.format(starred_changes(account_id), change_id)


def emails(account_id):
    """Return an URL to Gerrit for an account email

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return '{}/emails'.format(account(account_id))


def email(account_id, email_id):
    """Return an URL to Gerrit for an account email

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :param email_id: an email address, or preferred for the preferred email
        address of the user.
    :type email_id: str
    :rtype: str
    """

    return '{}/{}'.format(emails(account_id), email_id)


def preferred_email(account_id, email_id):
    """Return an URL to Gerrit

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :param email_id: an email address, or preferred for the preferred email
        address of the user.
    :type email_id: str
    :rtype: str
    """

    return '{}/preferred'.format(email(account_id, email_id))


def ssh_keys(account_id):
    """Return an URL to Gerrit for an account ssh keys

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return '{}/sshkeys'.format(account(account_id))


def ssh_key(account_id, ssh_key_id):
    """Return an URL to Gerrit for an account ssh key

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :param ssh_key_id: the sequence number of the SSH key
    :type ssh_key_id: str
    :rtype: str
    """

    return '{}/{}'.format(ssh_keys(account_id), ssh_key_id)


def capabilities(account_id):
    """Return an URL to Gerrit for an account capabilities

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return '{}/capabilities'.format(account(account_id))


def capability(account_id, capability_id):
    """Return an URL to Gerrit for an account capabilities

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :param capability_id: identifier of a global capability: valid values
        are all field names of the CapabilityInfo entity
    :type capability_id: str
    :rtype: str
    """

    return '{}/{}'.format(capabilities(account_id), capability_id)


def groups(account_id):
    """Return an URL to Gerrit for an account groups

    :param account_id: identifier that uniquely identifies one account
    :type account: str
    :rtype: str
    """

    return '{}/groups'.format(account(account_id))
