"""
This module encapsulate the Gerrit Code Review HTTP API protocol.
"""

import json
import logging

from libpycr.exceptions import NoSuchChangeError, PyCRError, RequestError
from libpycr.http import RequestFactory
from libpycr.utils.system import confirm, info


# pylint: disable=R0903
# Disable "Too few public methods"
class AccountInfo(object):
    """An account object."""

    def __init__(self, name=None, email=None):
        self.name = name
        self.email = email

    def __str__(self):
        # Email is not always available
        if not self.email:
            return self.name

        return '%s <%s>' % (self.name, self.email)

    @staticmethod
    def from_json(data):
        """
        Initialize a AccountInfo object and return it.

        PARAMETERS
            data: the JSON representation of the account as emitted by the
                Gerrit Code Review server (AccountInfo)

        RETURNS
            a AccountInfo object
        """

        account = AccountInfo(data['name'])

        # Email is not always available
        if 'email' in data:
            account.email = data['email']

        return account


# pylint: disable=R0902,R0903
# Disable "Too many instance attributes"
# Disable "Too few public methods"
class ChangeInfo(object):
    """A change object."""

    def __init__(self):
        self.uuid = None
        self.change_id = None
        self.legacy_id = None
        self.project = None
        self.branch = None
        self.subject = None
        self.owner = None

    @staticmethod
    def from_json(data):
        """
        Initialize a ChangeInfo object and return it.

        PARAMETERS
            data: the JSON representation of the change as emitted by the
                Gerrit Code Review server (ChangeInfo)

        RETURNS
            a ChangeInfo object
        """

        change = ChangeInfo()

        change.uuid = data['id']
        change.change_id = data['change_id']
        change.legacy_id = data['_number']
        change.project = data['project']
        change.branch = data['branch']
        change.subject = data['subject']
        change.owner = AccountInfo.from_json(data['owner'])

        return change


# pylint: disable=R0903
# Disable "Too few public methods"
class ReviewInfo(object):
    """A review object."""

    def __init__(self):
        self.reviewer = None
        self.approvals = None

    @staticmethod
    def from_json(data):
        """
        Initialize the ReviewInfo object and return it.

        PARAMETERS
            data: the JSON representation of the review as emitted by the
                Gerrit Code Review server (ReviewerInfo)
        """

        review = ReviewInfo()

        review.reviewer = AccountInfo.from_json(data)
        review.approvals = data['approvals'].items()

        return review


class Gerrit(object):
    """This object implements the Gerrit Code Review HTTP API low level
    routines.
    """

    # Logger
    log = logging.getLogger(__name__)

    @staticmethod
    def get_changes_endpoint(change_id, detailed=False):
        """
        Return an URL to the Gerrit Code Review server for the given change.


        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)
            detailed: request for a detailed view of the change

        RETURNS
            the URL as a string
        """

        return '%s/changes/%s%s' % (RequestFactory.get_remote_base_url(),
                                    change_id, '/detail' if detailed else '')

    @staticmethod
    def get_reviewers_endpoint(change_id):
        """
        Return an URL to the Gerrit Code Review server. This URL allows queries
        for reviewers of the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)

        RETURNS
            the URL as a string
        """

        return '%s/reviewers' % Gerrit.get_changes_endpoint(change_id)

    @staticmethod
    def get_reviewer_endpoint(change_id, account_id):
        """
        Return an URL to the Gerrit Code Review server. This URL allows queries
        for reviewers of the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)
            account_id: any identification string for an account (name,
                username, email)

        RETURNS
            the URL as a string
        """

        return '%s/%s' % (Gerrit.get_reviewers_endpoint(change_id), account_id)

    @classmethod
    def get_change(cls, change_id):
        """
        Send a GET request to the Gerrit Code Review server to fetch the data
        on the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID

        RETURNS
            a ChangeInfo object

        RAISES
            NoSuchChangeError if the change does not exist
            PyCRError on any other error
        """

        cls.log.debug('Change lookup: %s' % change_id)

        try:
            endpoint = Gerrit.get_changes_endpoint(change_id, detailed=True)
            _, response = RequestFactory.get(endpoint)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            raise PyCRError('cannot fetch change details', why)

        return ChangeInfo.from_json(response)

    @classmethod
    def get_reviews(cls, change_id):
        """
        Send a GET request to the Gerrit Code Review server to fetch the
        reviews for the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)

        RETURNS
            a Change object

        RAISES
            NoSuchChangeError if the change does not exist
            PyCRError on any other error
        """

        cls.log.debug('Reviews lookup: %s' % change_id)

        try:
            endpoint = Gerrit.get_reviewers_endpoint(change_id)
            _, response = RequestFactory.get(endpoint)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            raise PyCRError('unexpected error', why)

        # If 'approvals' field is missing, then this is no reviewer

        # NOTE: This seems to be against the specifications for this method:
        # https://gerrit-review.googlesource.com/Documentation/
        #   rest-api-changes.html#list-reviewers
        # "As result a list of ReviewerInfo entries is returned."
        # A ReviewerInfo entry is expected to have an "approvals" field, but
        # experiences show that it's not always the case, and that the change
        # owner can also be in the list although not a reviewers.

        return [ReviewInfo.from_json(r) for r in response if 'approvals' in r]

    @classmethod
    def add_reviewer(cls, change_id, account_id, force=False):
        """
        Send a POST request to the Gerrit Code Review server to add one user or
        all members of one group as reviewer to the change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)
            account_id: any identification string for an account (name,
                username, email)
            force: do not prompt the user for confirmation if gerrit needs a
                confirmation to add multiple reviewers at once (group).
                Defaults to False

        RETURNS
            The list of newly added reviewers on success, None otherwise

        RAISES
            PyCRError if the Gerrit server returns an error
        """

        cls.log.debug('Assign review to %s: %s' % (account_id, change_id))

        payload = {'reviewer': account_id}
        headers = {'content-type': 'application/json'}

        try:
            endpoint = Gerrit.get_reviewers_endpoint(change_id)
            _, response = RequestFactory.post(endpoint,
                                              data=json.dumps(payload),
                                              headers=headers)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            raise PyCRError('unexpected error', why)

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
                raise PyCRError('unexpected error', why)

        assert 'reviewers' in response, '"reviewers" not in HTTP response'
        return [AccountInfo.from_json(r) for r in response['reviewers']]

    @classmethod
    def get_reviewer(cls, change_id, account_id):
        """
        Send a GET request to the Gerrit Code Review server to fetch details
        about a reviewer of a change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)
            account_id: any identification string for an account (name,
                username, email)

        RETURNS
            a ReviewInfo object, None if the user is not a reviewer

        RAISES
            PyCRError if the Gerrit server returns an error
        """

        cls.log.debug('Reviewer lookup: "%s" for %s' %
                      (account_id, change_id))

        try:
            endpoint = Gerrit.get_reviewer_endpoint(change_id, account_id)
            _, response = RequestFactory.get(endpoint)

        except RequestError as why:
            if why.status_code == 404:
                # The user does not exist or is not a reviewer of the change
                return None

            raise PyCRError('unexpected error', why)

        return ReviewInfo.from_json(response)

    @classmethod
    def delete_reviewer(cls, change_id, account_id):
        """
        Send a DELETE request to the Gerrit Code Review server to delete one
        user from the reviewer's list of a change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)
            account_id: any identification string for an account (name,
                username, email)

        RAISES
            PyCRError if the Gerrit server returns an error
        """

        cls.log.debug('Delete reviewer: "%s" for %s' %
                      (account_id, change_id))

        try:
            endpoint = Gerrit.get_reviewer_endpoint(change_id, account_id)

            _, response = RequestFactory.get(endpoint)
            RequestFactory.delete(endpoint)

        except RequestError as why:
            if why.status_code == 403:
                raise PyCRError(
                    'no sufficient permissions or already submitted')

            if why.status_code == 404:
                # The user does not exist or is not a reviewer of the change
                return None

            raise PyCRError('unexpected error', why)

        assert len(response) == 1
        return ReviewInfo.from_json(response[0])
