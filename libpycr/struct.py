"""
This module contains all the Gerrit structure that can be received from the
server.
"""

from abc import ABCMeta, abstractmethod

from libpycr.utils.output import Formatter, Token, NEW_LINE


# pylint: disable=R0902,R0903
# Disable "Too many instance attributes" (for all above classes)
# Disable "Too few public methods" (for all above classes)
class Info(object):
    """Info interface."""

    __metaclass__ = ABCMeta

    def __str__(self):
        return Formatter.format(self.tokenize())

    @abstractmethod
    def tokenize(self):
        """
        Generate a stream of token.
        This method should be implemented as a Python generator.

        RETURNS
            a stream of tokens: tuple of (Token, string)
        """
        pass


class AccountInfo(Info):
    """An account object."""

    def __init__(self):
        self.name = None
        self.email = None
        self.username = None

    def tokenize(self):
        """Overrides."""

        # If email is available:
        #   John Doe <john@doe.com>
        # else:
        #   John Doe

        yield Token.Text, self.name

        if self.email:
            yield Token.Whitespace, ' '
            yield Token.Punctuation, '<'
            yield Token.Text, self.email
            yield Token.Punctuation, '>'

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

        account = AccountInfo()

        account.name = data['name']
        account.email = data.get('email', None)
        account.username = data.get('username', None)

        return account


class GitPersonInfo(Info):
    """A git person object."""

    def __init__(self):
        self.name = None
        self.email = None
        self.date = None
        self.timezone = None

    def tokenize(self):
        """Override."""

        # John Doe <john@doe.com>
        yield Token.Text, self.name
        yield Token.Whitespace, ' '
        yield Token.Punctuation, '<'
        yield Token.Text, self.email
        yield Token.Punctuation, '>'

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


class CommitInfo(Info):
    """A commit object."""

    def __init__(self):
        self.commit_id = None
        self.parents = None
        self.author = None
        self.committer = None
        self.subject = None
        self.message = None

    def tokenize(self):
        """Override."""

        # Commit-Id
        # commit a61970cc872b6f31953869450fc9c560257126e8
        yield Token.Generic.Heading, 'commit %s' % self.commit_id
        yield NEW_LINE

        # Parents
        # commit dee82bba6ab9add16c4d652f7c4d8e58e107c6ef
        if self.parents:
            for parent in self.parents:
                yield Token.TEXT, 'commit %s' % parent.commit_id
                yield NEW_LINE

        # Commit subject
        # Subject: Implement the REBASE command.
        yield Token.Text, 'Subject: %s' % self.subject
        yield NEW_LINE

        if self.author:
            yield Token.Text, 'Author:  %s' % self.author
            yield NEW_LINE

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
            commit.parents = []
            for parent in data['parent']:
                commit.parents.append(CommitInfo.parse(parent))

        if 'author' in data:
            commit.author = GitPersonInfo.parse(data['author'])
        if 'committer' in data:
            commit.committer = GitPersonInfo.parse(data['committer'])

        commit.message = data.get('message', None)

        return commit


class RevisionInfo(Info):
    """A revision object."""

    def __init__(self):
        self.draft = None
        self.has_draft_comments = None
        self.number = None
        self.fetch = None
        self.commit = None
        self.files = None
        self.actions = None

    def tokenize(self):
        """Override."""

        if self.commit:
            for token in self.commit.tokenize():
                yield token

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
        revision.number = data['_number']

        # self.fetch = FetchInfo.parse(data['fetch'])
        # self.files = FileInfo.parse(data['files'])
        # self.actions = ActionInfo.parse(data['action'])

        if 'commit' in data:
            revision.commit = CommitInfo.parse(data['commit'])

        return revision


class ChangeInfo(Info):
    """A change object."""

    MERGED = 'MERGED'
    SUBMITTED = 'SUBMITTED'

    def __init__(self):
        self.uuid = None
        self.change_id = None
        self.legacy_id = None
        self.project = None
        self.branch = None
        self.subject = None
        self.status = None
        self.owner = None
        self.revisions = None
        self.current_revision = None

    def tokenize(self):
        """Override."""

        yield Token.Generic.Heading, 'change-id %s' % self.change_id
        yield NEW_LINE
        yield Token.Text, 'Owner:   %s' % self.owner
        yield NEW_LINE
        yield Token.Text, 'Subject: %s' % self.subject

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

        change.status = data.get('status', None)
        change.current_revision = data.get('current_revision', None)

        if 'revisions' in data:
            change.revisions = {}

            for commit_id, details in data['revisions'].items():
                rev = RevisionInfo.parse(details)

                # The commit ID is not specified twice in the commit detail:
                # it needs to be set manually
                if rev.commit is not None:
                    rev.commit.commit_id = commit_id

                change.revisions[commit_id] = rev

        return change


class ReviewInfo(Info):
    """A review object."""

    def __init__(self):
        self.reviewer = None
        self.approvals = None

    def tokenize(self):
        """Override."""

        # Reviewer information
        #     Reviewer: John Doe <john@doe.com>
        yield Token.Text, '    Reviewer: '
        for token in self.reviewer.tokenize():
            yield token
        yield NEW_LINE

        # Review scores
        #     Code-Review: +2
        for label, score in self.approvals:
            if score in ('+1', '+2'):
                token = Token.Review.OK
            elif score in ('-1', '-2'):
                token = Token.Review.KO
            else:
                token = Token.Review.NONE

            yield Token.Text, '    %s: ' % label
            yield token, score
            yield NEW_LINE

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
