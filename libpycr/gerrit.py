"""
This module encapsulate the Gerrit Code Review HTTP API protocol.
"""

import json
import logging

from libpycr.exceptions import NoSuchChangeError, RebaseError, RequestError
from libpycr.exceptions import PyCRError, QueryError
from libpycr.http import RequestFactory, BASE64
from libpycr.struct import AccountInfo, ChangeInfo, ReviewInfo
from libpycr.utils.system import confirm, info


class Gerrit(object):
    """This object implements the Gerrit Code Review HTTP API low level
    routines.
    """

    # Logger
    log = logging.getLogger(__name__)

    @staticmethod
    def get_all_statuses():
        """
        Return the list of existing Gerrit Code Review statuses.

        RETURNS
            a iterable object of string
        """

        # List of valid Gerrit Code Review statuses
        return ('open', 'merged', 'abandoned', 'closed', 'reviewed',
                'submitted')

    @staticmethod
    def get_changes_query_endpoint():
        """
        Return an URL to the Gerrit Code Review server.

        RETURNS
            the URL as a string
        """

        return '%s/changes/' % RequestFactory.get_remote_base_url()

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

        return '%s%s%s' % (Gerrit.get_changes_query_endpoint(),
                           change_id, '/detail' if detailed else '')

    @staticmethod
    def get_revisions_endpoint(change_id, revision_id):
        """
        Return an URL to the Gerrit Code Review server. This URL allows queries
        to a specific reviesion of the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)
            revision_id: identifier that uniquely identifies one revision of a
                change (current, a commit ID (SHA1) or abbreviated commit ID,
                or a legacy numeric patch number)

        RETURNS
            the URL as a string
        """

        change_url = Gerrit.get_changes_endpoint(change_id)
        return '%s/revisions/%s' % (change_url, revision_id)

    @staticmethod
    def get_patch_endpoint(change_id, revision_id):
        """
        Return an URL to the Gerrit Code Review server. This URL allows queries
        for the patch of the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)
            revision_id: identifier that uniquely identifies one revision of a
                change (current, a commit ID (SHA1) or abbreviated commit ID,
                or a legacy numeric patch number)

        RETURNS
            the URL as a string
        """

        change_url = Gerrit.get_revisions_endpoint(change_id, revision_id)
        return '%s/patch' % change_url

    @staticmethod
    def get_rebase_endpoint(change_id, revision_id):
        """
        Return an URL to the Gerrit Code Review server. This URL allows queries
        to rebase the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)
            revision_id: identifier that uniquely identifies one revision of a
                change (current, a commit ID (SHA1) or abbreviated commit ID,
                or a legacy numeric patch number)

        RETURNS
            the URL as a string
        """

        change_url = Gerrit.get_revisions_endpoint(change_id, revision_id)
        return '%s/rebase' % change_url

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

    @staticmethod
    def forge_search_query(status=None, owner=None, reviewer=None):
        """
        Create a search query compatible with Gerrit Code Review queries.

        PARAMETERS
            status: the status of changes
            owner: the owner of changes
            reviewer: the reviewer of changes

        RETURNS
            the query as a string
        """

        buf = []

        if status is not None:
            buf.append('status:%s' % status)

        if owner is not None:
            buf.append('owner:%s' % owner)

        if reviewer is not None:
            buf.append('reviewer:%s' % reviewer)

        return '+'.join(buf)

    @classmethod
    def list_changes(cls, status='open', owner='self'):
        """
        Send a GET request to the Gerrit Code Review server to fetch the list
        of changes with the given STATUS and from the given OWNER.

        PARAMETERS
            status: the status of the change (open, merged, ...)
            owner: the account_id of the owner of the changes

        RETURNS
            a list of ChangeInfo

        RAISES
            NoSuchChangeError if no change match the query criterion
            PyCRError on any error
        """

        cls.log.debug(
            'Changes lookup with status:%s & owner:%s' % (status, owner))

        try:
            # NOTE: We can't use the params= parameter of the requests.get
            # method because this would encode the query string and prevent
            # Gerrit from parsing it

            endpoint = '%s?q=%s' % (Gerrit.get_changes_query_endpoint(),
                                    Gerrit.forge_search_query(status=status,
                                                              owner=owner))

            # DETAILED_ACCOUNTS option ensures that the owner email address is
            # sent in the response
            extra_params = {'o': 'DETAILED_ACCOUNTS'}

            _, response = RequestFactory.get(endpoint, params=extra_params)

        except RequestError as why:
            if why.status_code == 404:
                raise QueryError('no result for query criterion')

            raise PyCRError('cannot fetch change details', why)

        return [ChangeInfo.parse(c) for c in response]

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

        return ChangeInfo.parse(response)

    @classmethod
    def get_patch(cls, change_id, revision_id='current'):
        """
        Send a GET request to the Gerrit Code Review server to fetch the
        patch for the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)
            revision_id: identifier that uniquely identifies one revision of a
                change (current, a commit ID (SHA1) or abbreviated commit ID,
                or a legacy numeric patch number)

        RETURNS
            the diff as a string

        RAISES
            NoSuchChangeError if the change does not exist
            PyCRError on any other error
        """

        cls.log.debug('Fetch diff: %s (revision: %s)' %
                      (change_id, revision_id))

        try:
            endpoint = Gerrit.get_patch_endpoint(change_id, revision_id)
            _, patch = RequestFactory.get(endpoint, encoding=BASE64)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            raise PyCRError('unexpected error', why)

        return patch

    @classmethod
    def rebase(cls, change_id, revision_id='current'):
        """
        Send a GET request to the Gerrit Code Review server to rebase the
        given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)
            revision_id: identifier that uniquely identifies one revision of a
                change (current, a commit ID (SHA1) or abbreviated commit ID,
                or a legacy numeric patch number)

        RAISES
            NoSuchChangeError if the change does not exist
            PyCRError on any other error
        """

        cls.log.debug('rebase: %s (revision: %s)' % (change_id, revision_id))

        try:
            endpoint = Gerrit.get_rebase_endpoint(change_id, revision_id)
            _, change = RequestFactory.post(endpoint)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            if why.status_code == 409:
                # There was a conflict rebasing the change
                # Error message is return as PLAIN text
                raise RebaseError(why.response.text.strip())

            raise PyCRError('unexpected error', why)

        return ChangeInfo.parse(change)

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

        return [ReviewInfo.parse(r) for r in response if 'approvals' in r]

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
        return [AccountInfo.parse(r) for r in response['reviewers']]

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

        return ReviewInfo.parse(response)

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
        return ReviewInfo.parse(response[0])
