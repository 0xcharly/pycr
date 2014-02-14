"""
This module contains all the Gerrit structure that can be received from the
server.
"""


# pylint: disable=R0902,R0903
# Disable "Too few public methods" (for all above classes)
# Disable "Too many instance attributes" (for all above classes)
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
    def parse(data):
        """
        Initialize a AccountInfo object and return it.

        PARAMETERS
            data: the JSON representation of the account as emitted by the
                Gerrit Code Review server (AccountInfo)

        RETURNS
            a AccountInfo object
        """

        account = AccountInfo(data['name'])
        account.email = data.get('email', None)

        return account


class GitPersonInfo(object):
    """A git person object."""

    def __init__(self):
        self.name = None
        self.email = None
        self.date = None
        self.timezone = None

    @staticmethod
    def parse(data):
        """
        Initialize a GitPersonInfo object and return it.

        PARAMETERS
            data: the JSON representation of the change as emitted by the
                Gerrit Code Review server (GitPersonInfo)

        RETURNS
            a GitPersonInfo object
        """

        person = GitPersonInfo()

        person.name = data['name']
        person.email = data['email']
        person.date = data['date']
        person.timezone = data['tz']

        return person


class CommitInfo(object):
    """A commit object."""

    def __init__(self):
        self.commit_id = None
        self.parent = None
        self.author = None
        self.committer = None
        self.subject = None
        self.message = None

    @staticmethod
    def parse(data):
        """
        Initialize a CommitInfo object and return it.

        PARAMETERS
            data: the JSON representation of the change as emitted by the
                Gerrit Code Review server (CommitInfo)

        RETURNS
            a CommitInfo object
        """

        commit = CommitInfo()

        commit.commit_id = data.get('commit', None)
        commit.subject = data['subject']

        if 'parent' in data:
            commit.parent = []
            for parent in data['parent']:
                commit.parent.append(CommitInfo.parse(parent))

        if 'author' in data:
            commit.author = GitPersonInfo.parse(data['author'])
        if 'committer' in data:
            commit.committer = GitPersonInfo.parse(data['committer'])

        commit.message = data.get('message', None)

        return commit


class RevisionInfo(object):
    """A revision object."""

    def __init__(self):
        self.draft = None
        self.has_draft_comments = None
        self.number = None
        self.fetch = None
        self.commit = None
        self.files = None
        self.actions = None

    @staticmethod
    def parse(data):
        """
        Initialize a CommitInfo object and return it.

        PARAMETERS
            data: the JSON representation of the change as emitted by the
                Gerrit Code Review server (CommitInfo)

        RETURNS
            a CommitInfo object
        """

        revision = RevisionInfo()

        revision.draft = data.get('draft', False)
        revision.has_draft_comments = data.get('has_draft_comments', False)
        revision.number = data['number']

        # self.fetch = FetchInfo.parse(data['fetch'])
        # self.files = FileInfo.parse(data['files'])
        # self.actions = ActionInfo.parse(data['action'])

        if 'commit' in data:
            revision.commit = CommitInfo.parse(data['commit'])

        return revision


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
        self.revisions = None
        self.current_revision = None

    @staticmethod
    def parse(data):
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
        change.owner = AccountInfo.parse(data['owner'])

        change.current_revision = data.get('current_revision', None)

        if 'revisions' in data:
            change.revisions = {}

            for commit_id, details in data['revisions']:
                rev = RevisionInfo(details)
                # The commit ID is not specified twice in the commit detail:
                # it needs to be set manually
                rev.commit.commit_id = commit_id
                change.revisions[commit_id] = rev

        return change


class ReviewInfo(object):
    """A review object."""

    def __init__(self):
        self.reviewer = None
        self.approvals = None

    @staticmethod
    def parse(data):
        """
        Initialize the ReviewInfo object and return it.

        PARAMETERS
            data: the JSON representation of the review as emitted by the
                Gerrit Code Review server (ReviewerInfo)
        """

        review = ReviewInfo()

        review.reviewer = AccountInfo.parse(data)
        review.approvals = data['approvals'].items()

        return review
