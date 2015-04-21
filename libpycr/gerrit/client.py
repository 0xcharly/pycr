"""Gerrit Code Review HTTP API client"""

import json
import logging

from libpycr.exceptions import (
    ConflictError, NoSuchChangeError, RequestError, UnexpectedError)
from libpycr.exceptions import PyCRError, QueryError
from libpycr.http import RequestFactory, BASE64
from libpycr.gerrit.api import accounts, changes
from libpycr.gerrit.entities import (
    AccountInfo, CapabilityInfo, ChangeInfo, DiffPreferencesInfo, EmailInfo,
    GroupInfo, ReviewInfo, ReviewerInfo, SshKeyInfo)
from libpycr.utils.system import confirm, info


class Gerrit(object):
    """Provides Gerrit Code Review HTTP low level API implementation"""

    # Logger
    log = logging.getLogger(__name__)

    # Valid scores for a code review
    SCORES = ('-2', '-1', '0', '+1', '+2')

    @staticmethod
    def get_all_statuses():
        """Return the list of existing Gerrit Code Review statuses

        :rtype: collections.iterable[str]
        """

        # List of valid Gerrit Code Review statuses
        return ('open', 'merged', 'abandoned', 'closed', 'reviewed',
                'submitted')

    @classmethod
    def list_watched_changes(cls, status='open'):
        """List user's watched changes

        Sends a GET request to Gerrit to fetch the list of changes with the
        given STATUS and from the given OWNER.

        :param status: the status of the change (open, merged, ...)
        :type status: str
        :param owner: the account_id of the owner of the changes
        :type owner: str
        :rtype: tuple[ChangeInfo]
        :raise: NoSuchChangeError if no change match the query criterion
        :raise: PyCRError on any other error
        """

        cls.log.debug('Watched changes lookup with status:%s', status)

        try:
            endpoint = changes.search_query(status=status, watched=True)

            # DETAILED_ACCOUNTS option ensures that the owner email address is
            # sent in the response
            extra_params = {'o': 'DETAILED_ACCOUNTS'}

            _, response = RequestFactory.get(endpoint, params=extra_params)

        except RequestError as why:
            if why.status_code == 404:
                raise QueryError('no result for query criterion')

            raise UnexpectedError(why)

        return tuple([ChangeInfo.parse(c) for c in response])

    @classmethod
    def list_changes(cls, status='open', owner='self'):
        """List changes

        Sends a GET request to Gerrit to fetch the list of changes with the
        given STATUS and from the given OWNER.

        :param status: the status of the change (open, merged, ...)
        :type status: str
        :param owner: the account_id of the owner of the changes
        :type owner: str
        :rtype: tuple[ChangeInfo]
        :raise: NoSuchChangeError if no change match the query criterion
        :raise: PyCRError on any other error
        """

        cls.log.debug(
            'Changes lookup with status:%s & owner:%s', status, owner)

        try:
            endpoint = changes.search_query(status=status, owner=owner)

            # DETAILED_ACCOUNTS option ensures that the owner email address is
            # sent in the response
            extra_params = {'o': 'DETAILED_ACCOUNTS'}

            _, response = RequestFactory.get(endpoint, params=extra_params)

        except RequestError as why:
            if why.status_code == 404:
                raise QueryError('no result for query criterion')

            raise UnexpectedError(why)

        return tuple([ChangeInfo.parse(c) for c in response])

    @classmethod
    def get_change(cls, change_id):
        """Fetch a change details

        Sends a GET request to Gerrit to fetch the data on the given change.

        :param change_id: any identification number for the change (UUID,
            Change-Id, or legacy numeric change ID
        :type change_id: str
        :rtype: ChangeInfo
        :raise: NoSuchChangeError if the change does not exists
        :raise: PyCRError on any other error
        """

        cls.log.debug('Change lookup: %s', change_id)

        try:
            endpoint = changes.detailed_changes(change_id)

            # CURRENT_REVISION describe the current revision (patch set) of the
            # change, including the commit SHA-1 and URLs to fetch from
            extra_params = {'o': 'CURRENT_REVISION'}

            _, response = RequestFactory.get(endpoint, params=extra_params)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            raise UnexpectedError(why)

        return ChangeInfo.parse(response)

    @classmethod
    def get_patch(cls, change_id, revision_id='current'):
        """Fetch a patch content

        Sends a GET request to Gerrit to fetch the patch for the given change.
        Returns the diff content.

        :param change_id: any identification number for the change (UUID,
            Change-Id, or legacy numeric change ID)
        :type change_id: str
        :param revision_id: identifier that uniquely identifies one revision of
            a change (current, a commit ID (SHA1) or abbreviated commit ID, or
            a legacy numeric patch number)
        :type revision_id: str
        :rtype: str
        :raise: NoSuchChangeError if the change does not exists
        :raise: PyCRError on any other error
        """

        cls.log.debug('Fetch diff: %s (revision: %s)', change_id, revision_id)

        try:
            endpoint = changes.patch(change_id, revision_id)
            _, patch = RequestFactory.get(endpoint, encoding=BASE64)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            raise UnexpectedError(why)

        return patch

    @classmethod
    def set_review(cls, score, message, change_id, label,
                   revision_id='current'):
        """Set a review score

        Sends a POST request to Gerrit to review the given change.

        :param score: the score (-2, -1, 0, +1, +2)
        :type score: str
        :param message: the review message
        :type message: str
        :param change_id: any identification number for the change (UUID,
            Change-Id, or legacy numeric change ID)
        :type change_id: str
        :param label: the label to score
        :type label: str
        :param revision_id: identifier that uniquely identifies one revision of
            a change (current, a commit ID (SHA1) or abbreviated commit ID, or
            a legacy numeric patch number)
        :type revision_id: str
        :rtype: ChangeInfo
        :raise: NoSuchChangeError if the change does not exists
        :raise: PyCRError on any other error
        """

        cls.log.debug('Set review: %s (revision: %s)', change_id, revision_id)
        cls.log.debug('Score:   %s', score)
        cls.log.debug('Label:   %s', label)
        cls.log.debug('Message: %s', message)

        assert score in Gerrit.SCORES

        payload = {
            'message': message,
            'labels': {label: score}
        }
        headers = {'content-type': 'application/json'}

        try:
            endpoint = changes.review(change_id, revision_id)
            _, review = RequestFactory.post(endpoint,
                                            data=json.dumps(payload),
                                            headers=headers)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            if why.status_code == 400:
                raise QueryError(
                    'invalid score "%s" for label "%s"' % (score, label))

            raise UnexpectedError(why)

        return ReviewInfo.parse(review)

    @classmethod
    def rebase(cls, change_id):
        """Rebase a change

        Sends a POST request to Gerrit to rebase the given change.

        :param change_id: any identification number for the change (UUID,
            Change-Id, or legacy numeric change ID)
        :type change_id: str
        :rtype: ChangeInfo
        :raise: NoSuchChangeError if the change does not exists
        :raise: ConflictError if could not rebase the change
        :raise: PyCRError on any other error
        """

        cls.log.debug('rebase: %s', change_id)

        try:
            _, change = RequestFactory.post(changes.rebase(change_id))

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            if why.status_code == 409:
                # There was a conflict rebasing the change
                # Error message is return as PLAIN text
                raise ConflictError(why.response.text.strip())

            raise UnexpectedError(why)

        return ChangeInfo.parse(change)

    @classmethod
    def submit(cls, change_id):
        """Submit a change

        Sends a POST request to Gerrit to submit the given change. Returns True
        if the change was successfully merged, False otherwise.

        :param change_id: any identification number for the change (UUID,
            Change-Id, or legacy numeric change ID)
        :type change_id: str
        :rtype: bool
        :raise: NoSuchChangeError if the change does not exists
        :raise: ConflictError if could not submit the change
        :raise: PyCRError on any other error
        """

        cls.log.debug('submit: %s', change_id)

        payload = {'wait_for_merge': True}
        headers = {'content-type': 'application/json'}

        try:
            _, change = RequestFactory.post(changes.submit(change_id),
                                            data=json.dumps(payload),
                                            headers=headers)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            if why.status_code == 409:
                # There was a conflict rebasing the change
                # Error message is return as PLAIN text
                raise ConflictError(why.response.text.strip())

            raise UnexpectedError(why)

        return ChangeInfo.parse(change).status == ChangeInfo.MERGED

    @classmethod
    def get_reviews(cls, change_id):
        """Fetch the reviews for a change

        Sends a GET request to Gerrit to fetch the reviews for the given
        change.

        :param change_id: any identification number for the change (UUID,
            Change-Id, or legacy numeric change ID)
        :type change_id: str
        :rtype: tuple[ReviewerInfo]
        :raise: NoSuchChangeError if the change does not exists
        :raise: PyCRError on any other error
        """

        cls.log.debug('Reviews lookup: %s', change_id)

        try:
            endpoint = changes.reviewers(change_id)
            _, response = RequestFactory.get(endpoint)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            raise UnexpectedError(why)

        # If 'approvals' field is missing, then there is no reviewer

        # NOTE: This seems to be against the specifications for this method:
        # https://gerrit-review.googlesource.com/Documentation/
        #   rest-api-changes.html#list-reviewers
        # "As result a list of ReviewerInfo entries is returned."
        # A ReviewerInfo entry is expected to have an "approvals" field, but
        # experiences show that it's not always the case, and that the change
        # owner can also be in the list although not a reviewers.

        return tuple(
            [ReviewerInfo.parse(r) for r in response if 'approvals' in r])

    @classmethod
    def add_reviewer(cls, change_id, account_id, force=False):
        """Add a reviewer

        Sends a POST request to Gerrit to add one user or all members of one
        group as reviewer to the change.

        :param change_id: any identification number for the change (UUID,
            Change-Id, or legacy numeric change ID)
        :type change_id: str
        :param account_id: any identification string for an account (name,
            username, email)
        :type account_id: str
        :param force: do not prompt the user for confirmation if gerrit needs a
            confirmation to add multiple reviewers at once (group).  Defaults
            to False
        :type force: bool
        :rtype: tuple(AccountInfo)
        :raise: PyCRError if the Gerrit server returns an error
        """

        cls.log.debug('Assign review to %s: %s', account_id, change_id)

        payload = {'reviewer': account_id}
        headers = {'content-type': 'application/json'}

        try:
            endpoint = changes.reviewers(change_id)
            _, response = RequestFactory.post(endpoint,
                                              data=json.dumps(payload),
                                              headers=headers)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            raise UnexpectedError(why)

        if 'confirm' in response:
            assert 'error' in response, 'missing "error" field in response'

            cls.log.debug('Assigning review: confirmation requested')

            do_add_reviewers = True if force else confirm(response['error'])

            if not do_add_reviewers:
                info('reviewer not added, aborting...')
                return None

            try:
                payload['confirmed'] = True
                _, response = RequestFactory.post(endpoint,
                                                  data=json.dumps(payload),
                                                  headers=headers)

            except RequestError as why:
                raise UnexpectedError(why)

        assert 'reviewers' in response, '"reviewers" not in HTTP response'
        return tuple([AccountInfo.parse(r) for r in response['reviewers']])

    @classmethod
    def get_reviewer(cls, change_id, account_id):
        """Fetch a reviewer info

        Sends a GET request to Gerrit to fetch details about a reviewer of a
        change. Returns None if the reviewer does not exists or is not a
        reviewer of the change.

        :param change_id: any identification number for the change (UUID,
            Change-Id, or legacy numeric change ID)
        :type change_id: str
        :param account_id: any identification string for an account (name,
            username, email)
        :type account_id: str
        :rtype: ReviewerInfo | None
        :raise: PyCRError if the Gerrit server returns an error
        """

        cls.log.debug('Reviewer lookup: "%s" for %s', account_id, change_id)

        try:
            endpoint = changes.reviewer(change_id, account_id)
            _, response = RequestFactory.get(endpoint)

        except RequestError as why:
            if why.status_code == 404:
                # The user does not exist or is not a reviewer of the change
                return None

            raise UnexpectedError(why)

        return ReviewerInfo.parse(response)

    @classmethod
    def delete_reviewer(cls, change_id, account_id):
        """Remove a reviewer from the list of reviewer of a change

        Sends a DELETE request to Gerrit to delete one user from the reviewer's
        list of a change. Returns None if the reviewer does not exists or is
        not a reviewer of the change.

        :param change_id: any identification number for the change (UUID,
            Change-Id, or legacy numeric change ID)
        :type change_id: str
        :param account_id: any identification string for an account (name,
            username, email)
        :type account_id: str
        :rtype: ReviewerInfo | None
        :raise: PyCRError if the Gerrit server returns an error
        """

        cls.log.debug('Delete reviewer: "%s" for %s', account_id, change_id)

        try:
            endpoint = changes.reviewer(change_id, account_id)

            _, response = RequestFactory.get(endpoint)
            RequestFactory.delete(endpoint)

        except RequestError as why:
            if why.status_code == 403:
                raise PyCRError(
                    'no sufficient permissions or already submitted')

            if why.status_code == 404:
                # The user does not exist or is not a reviewer of the change
                return None

            raise UnexpectedError(why)

        assert len(response) == 1
        return ReviewerInfo.parse(response[0])

    @classmethod
    def get_account(cls, account_id='self'):
        """Fetch Gerrit account details

        :param account_id: identifier that uniquely identifies one account
        :type account: str
        :rtype: AccountInfo
        :raise: PyCRError on any other error
        """

        cls.log.debug('List Gerrit accounts')

        try:
            _, response = RequestFactory.get(accounts.account(account_id))

        except RequestError as why:
            if why.status_code == 404:
                raise QueryError('no such account')

            raise UnexpectedError(why)

        return AccountInfo.parse(response)

    @classmethod
    def get_emails(cls, account_id='self'):
        """Fetch Gerrit account emails

        :param account_id: identifier that uniquely identifies one account
        :type account: str
        :rtype: tuple[EmailInfo]
        :raise: PyCRError on any other error
        """

        cls.log.debug('List Gerrit account emails')

        try:
            _, response = RequestFactory.get(accounts.emails(account_id))

        except RequestError as why:
            if why.status_code == 404:
                raise QueryError('no such account')

            raise UnexpectedError(why)

        return tuple([EmailInfo.parse(e) for e in response])

    @classmethod
    def get_ssh_keys(cls, account_id='self'):
        """Fetch Gerrit account SSH keys

        :param account_id: identifier that uniquely identifies one account
        :type account: str
        :rtype: tuple[SshKeyInfo]
        :raise: PyCRError on any other error
        """

        cls.log.debug('List Gerrit account SSH keys')

        try:
            _, response = RequestFactory.get(accounts.ssh_keys(account_id))

        except RequestError as why:
            if why.status_code == 404:
                raise QueryError('no such account')

            raise UnexpectedError(why)

        return tuple([SshKeyInfo.parse(k) for k in response])

    @classmethod
    def get_ssh_key(cls, account_id='self', ssh_key_id='0'):
        """Fetch Gerrit account SSH key

        :param account_id: identifier that uniquely identifies one account
        :type account: str
        :param ssh_key_id: unique identifier to a SSH key
        :type ssh_key_id: int
        :rtype: SshKeyInfo
        :raise: PyCRError on any other error
        """

        cls.log.debug('List Gerrit account SSH keys')

        try:
            _, response = RequestFactory.get(
                accounts.ssh_key(account_id, ssh_key_id))

        except RequestError as why:
            if why.status_code == 404:
                raise QueryError('no such account or ssh key')

            raise UnexpectedError(why)

        return SshKeyInfo.parse(response)

    @classmethod
    def get_capabilities(cls, account_id='self'):
        """Fetch Gerrit account capabilities

        :param account_id: identifier that uniquely identifies one account
        :type account: str
        :rtype: CapabilityInfo
        :raise: PyCRError on any other error
        """

        cls.log.debug('List Gerrit account capabilities')

        try:
            _, response = RequestFactory.get(accounts.capabilities(account_id))

        except RequestError as why:
            if why.status_code == 404:
                raise QueryError('no such account')

            raise UnexpectedError(why)

        return CapabilityInfo.parse(response)

    @classmethod
    def get_diff_prefs(cls, account_id='self'):
        """Fetch Gerrit account diff preferences

        :param account_id: identifier that uniquely identifies one account
        :type account: str
        :rtype: DiffPreferencesInfo
        :raise: PyCRError on any other error
        """

        cls.log.debug('List Gerrit account diff preferences')

        try:
            _, response = RequestFactory.get(
                accounts.diff_preferences(account_id))

        except RequestError as why:
            if why.status_code == 404:
                raise QueryError('no such account')

            raise UnexpectedError(why)

        return DiffPreferencesInfo.parse(response)

    @classmethod
    def get_starred_changes(cls, account_id='self'):
        """Fetch Gerrit account starred changes

        :param account_id: identifier that uniquely identifies one account
        :type account: str
        :rtype: tuple[ChangeInfo]
        :raise: PyCRError on any other error
        """

        cls.log.debug('List Gerrit account starred changes')

        try:
            _, response = RequestFactory.get(
                accounts.starred_changes(account_id))

        except RequestError as why:
            if why.status_code == 404:
                raise QueryError('no such account')

            raise UnexpectedError(why)

        return tuple([ChangeInfo.parse(c) for c in response])

    @classmethod
    def get_groups(cls, account_id='self'):
        """Fetch Gerrit account groups

        :param account_id: identifier that uniquely identifies one account
        :type account: str
        :rtype: tuple[GroupInfo]
        :raise: PyCRError on any other error
        """

        cls.log.debug('List Gerrit account group')

        try:
            _, response = RequestFactory.get(accounts.groups(account_id))

        except RequestError as why:
            if why.status_code == 404:
                raise QueryError('no such account')

            raise UnexpectedError(why)

        return tuple([GroupInfo.parse(g) for g in response])
