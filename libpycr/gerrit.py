"""
This module encapsulate the Gerrit Code Review HTTP API protocol.
"""

import json
import logging

from libpycr.exceptions import NoSuchChangeError, ConflictError, RequestError
from libpycr.exceptions import PyCRError, QueryError
from libpycr.http import RequestFactory, BASE64
from libpycr.struct import AccountInfo, ChangeInfo, ReviewInfo, ReviewerInfo
from libpycr.utils.system import confirm, info


class Api(object):
    """This object contains the various endpoints to the Gerrit Code Review
    API.
    """

    @staticmethod
    def changes_query():
        """
        Return an URL to the Gerrit Code Review server.

        RETURNS
            the URL as a string
        """

        return '%s/changes/' % RequestFactory.get_remote_base_url()

    @staticmethod
    def changes(change_id):
        """
        Return an URL to the Gerrit Code Review server for the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)

        RETURNS
            the URL as a string
        """

        return '%s%s' % (Api.changes_query(), change_id)

    @staticmethod
    def detailed_changes(change_id):
        """
        Return an URL to the Gerrit Code Review server for the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)

        RETURNS
            the URL as a string
        """

        return '%s/detail' % Api.changes(change_id)

    @staticmethod
    def revisions(change_id, revision_id):
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

        return '%s/revisions/%s' % (Api.changes(change_id), revision_id)

    @staticmethod
    def patch(change_id, revision_id):
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

        return '%s/patch' % Api.revisions(change_id, revision_id)

    @staticmethod
    def review(change_id, revision_id):
        """
        Return an URL to the Gerrit Code Review server. This URL allows queries
        to set a review for the given revision of a change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)
            revision_id: identifier that uniquely identifies one revision of a
                change (current, a commit ID (SHA1) or abbreviated commit ID,
                or a legacy numeric patch number)

        RETURNS
            the URL as a string
        """

        return '%s/review' % Api.revisions(change_id, revision_id)

    @staticmethod
    def rebase(change_id):
        """
        Return an URL to the Gerrit Code Review server. This URL allows queries
        to rebase the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)

        RETURNS
            the URL as a string
        """

        return '%s/rebase' % Api.changes(change_id)

    @staticmethod
    def submit(change_id):
        """
        Return an URL to the Gerrit Code Review server. This URL allows queries
        to submit the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)

        RETURNS
            the URL as a string
        """

        return '%s/submit' % Api.changes(change_id)

    @staticmethod
    def reviewers(change_id):
        """
        Return an URL to the Gerrit Code Review server. This URL allows queries
        for reviewers of the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)

        RETURNS
            the URL as a string
        """

        return '%s/reviewers' % Api.changes(change_id)

    @staticmethod
    def reviewer(change_id, account_id):
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

        return '%s/%s' % (Api.reviewers(change_id), account_id)

    @staticmethod
    def search_query_attr(status=None, owner=None, reviewer=None,
                          watched=None):
        """
        Create a search query compatible with Gerrit Code Review queries.

        PARAMETERS
            status: the status of changes
            owner: the owner of changes
            reviewer: the reviewer of changes
            watched: whether the change should be in the watched list or not

        RETURNS
            the query parameters as a string
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

    @staticmethod
    def search_query(status=None, owner=None, reviewer=None, watched=None):
        """
        Return an URL to the Gerrit Code Review server. This URL contains the
        query to perform.

        PARAMETERS
            status: the status of changes
            owner: the owner of changes
            reviewer: the reviewer of changes

        RETURNS
            the query URL as a string
        """

        # NOTE: We can't use the params= parameter of the requests.get
        # method because this would encode the query string and prevent
        # Gerrit from parsing it

        return '%s?q=%s' % (Api.changes_query(),
                            Api.search_query_attr(status=status, owner=owner,
                                                  reviewer=reviewer,
                                                  watched=watched))


class Gerrit(object):
    """This object implements the Gerrit Code Review HTTP API low level
    routines.
    """

    # Logger
    log = logging.getLogger(__name__)

    # Valid scores for a code review
    SCORES = ('-2', '-1', '0', '+1', '+2')

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

    @classmethod
    def list_watched_changes(cls, status='open'):
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

        cls.log.debug('Watched changes lookup with status:%s' % status)

        try:
            endpoint = Api.search_query(status=status, watched=True)

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
            endpoint = Api.search_query(status=status, owner=owner)

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
            a ChangeInfo

        RAISES
            NoSuchChangeError if the change does not exist
            PyCRError on any other error
        """

        cls.log.debug('Change lookup: %s' % change_id)

        try:
            endpoint = Api.detailed_changes(change_id)

            # CURRENT_REVISION describe the current revision (patch set) of the
            # change, including the commit SHA-1 and URLs to fetch from
            extra_params = {'o': 'CURRENT_REVISION'}

            _, response = RequestFactory.get(endpoint, params=extra_params)

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
            endpoint = Api.patch(change_id, revision_id)
            _, patch = RequestFactory.get(endpoint, encoding=BASE64)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            raise PyCRError('unexpected error', why)

        return patch

    @classmethod
    def set_review(cls, score, message, change_id, revision_id='current'):
        """
        Send a POST request to the Gerrit Code Review server to review the
        given change.

        PARAMETERS
            score: the score (-2, -1, 0, +1, +2)
            message: the review message
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)
            revision_id: identifier that uniquely identifies one revision of a
                change (current, a commit ID (SHA1) or abbreviated commit ID,
                or a legacy numeric patch number)

        RETURNS
            a ChangeInfo

        RAISES
            NoSuchChangeError if the change does not exist
            PyCRError on any other error
        """

        cls.log.debug('Set review: %s (revision: %s)' %
                      (change_id, revision_id))
        cls.log.debug('Score:   %s', score)
        cls.log.debug('Message: %s', message)

        assert score in Gerrit.SCORES

        payload = {
            'message': message,
            'labels': {'Code-Review': score}
        }
        headers = {'content-type': 'application/json'}

        try:
            endpoint = Api.review(change_id, revision_id)
            _, review = RequestFactory.post(endpoint,
                                            data=json.dumps(payload),
                                            headers=headers)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            raise PyCRError('unexpected error', why)

        return ReviewInfo.parse(review)

    @classmethod
    def rebase(cls, change_id):
        """
        Send a POST request to the Gerrit Code Review server to rebase the
        given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)

        RETURNS
            a ChangeInfo

        RAISES
            NoSuchChangeError if the change does not exist
            ConflictError if could not submit the change
            PyCRError on any other error
        """

        cls.log.debug('rebase: %s' % change_id)

        try:
            _, change = RequestFactory.post(Api.rebase(change_id))

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            if why.status_code == 409:
                # There was a conflict rebasing the change
                # Error message is return as PLAIN text
                raise ConflictError(why.response.text.strip())

            raise PyCRError('unexpected error', why)

        return ChangeInfo.parse(change)

    @classmethod
    def submit(cls, change_id):
        """
        Send a POST request to the Gerrit Code Review server to submit the
        given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)

        RETURNS
            True if the change was successfully merged, False otherwise

        RAISES
            NoSuchChangeError if the change does not exist
            ConflictError if could not submit the change
            PyCRError on any other error
        """

        cls.log.debug('submit: %s' % change_id)

        payload = {'wait_for_merge': True}
        headers = {'content-type': 'application/json'}

        try:
            _, change = RequestFactory.post(Api.submit(change_id),
                                            data=json.dumps(payload),
                                            headers=headers)

        except RequestError as why:
            if why.status_code == 404:
                raise NoSuchChangeError(change_id)

            if why.status_code == 409:
                # There was a conflict rebasing the change
                # Error message is return as PLAIN text
                raise ConflictError(why.response.text.strip())

            raise PyCRError('unexpected error', why)

        return ChangeInfo.parse(change).status == ChangeInfo.MERGED

    @classmethod
    def get_reviews(cls, change_id):
        """
        Send a GET request to the Gerrit Code Review server to fetch the
        reviews for the given change.

        PARAMETERS
            change_id: any identification number for the change (UUID,
                Change-Id, or legacy numeric change ID)

        RETURNS
            a ChangeInfo

        RAISES
            NoSuchChangeError if the change does not exist
            PyCRError on any other error
        """

        cls.log.debug('Reviews lookup: %s' % change_id)

        try:
            endpoint = Api.reviewers(change_id)
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

        return [ReviewerInfo.parse(r) for r in response if 'approvals' in r]

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
            endpoint = Api.reviewers(change_id)
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
            endpoint = Api.reviewer(change_id, account_id)
            _, response = RequestFactory.get(endpoint)

        except RequestError as why:
            if why.status_code == 404:
                # The user does not exist or is not a reviewer of the change
                return None

            raise PyCRError('unexpected error', why)

        return ReviewerInfo.parse(response)

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

        RETURNS
            a ReviewInfo

        RAISES
            PyCRError if the Gerrit server returns an error
        """

        cls.log.debug('Delete reviewer: "%s" for %s' %
                      (account_id, change_id))

        try:
            endpoint = Api.reviewer(change_id, account_id)

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
        return ReviewerInfo.parse(response[0])
