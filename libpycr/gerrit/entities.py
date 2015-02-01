"""Provides all the Gerrit structure that can be received from the server"""

from abc import ABCMeta, abstractmethod

from libpycr.utils.output import Formatter, NEW_LINE, Token


# pylint: disable=R0902,R0903
# Disable "Too many instance attributes" (for all above classes)
# Disable "Too few public methods" (for all above classes)
class Info(object):
    """Info interface"""

    __metaclass__ = ABCMeta

    def __str__(self):
        return Formatter.format(self.tokenize())

    def raw_str(self):
        """Return a simple string (no formatting)

        :rtype: str
        """
        return Formatter.raw_format(self.tokenize())

    @abstractmethod
    def tokenize(self):
        """Generate a stream of token

        This method should be implemented as a Python generator.

        :rtype: tuple(Token, string)
        """
        pass


class AccountInfo(Info):
    """An account object"""

    def __init__(self):
        self.name = None
        self.email = None
        self.username = None

    def __hash__(self):
        # A username is expected to be unique
        return hash(self.username)

    def __cmp__(self, other):
        # Both __hash__ and __cmp__ are needed for set() to uniquify a list of
        # AccountInfo.
        return cmp(self.username, other.username)

    def tokenize(self):
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
        """Create an initialized AccountInfo object

        :param data: JSON representation of the account as emitted by Gerrit
        :type data: str
        :rtype: AccountInfo
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
        # John Doe <john@doe.com>
        yield Token.Text, self.name
        yield Token.Whitespace, ' '
        yield Token.Punctuation, '<'
        yield Token.Text, self.email
        yield Token.Punctuation, '>'

    @staticmethod
    def parse(data):
        """Create an initialized GitPersonInfo object

        :param data: JSON representation of the git person as emitted by Gerrit
        :type data: str
        :rtype: GitPersonInfo
        """

        person = GitPersonInfo()

        person.name = data['name']
        person.email = data['email']
        person.date = data['date']
        person.timezone = data['tz']

        return person


class CommitInfo(Info):
    """A commit object"""

    def __init__(self):
        self.commit_id = None
        self.parents = None
        self.author = None
        self.committer = None
        self.subject = None
        self.message = None

    def tokenize(self):
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
        """Create an initialized CommitInfo object

        :param data: JSON representation of the commit as emitted by Gerrit
        :type data: str
        :rtype: CommitInfo
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
    """A revision object"""

    def __init__(self):
        self.draft = None
        self.has_draft_comments = None
        self.number = None
        self.fetch = None
        self.commit = None
        self.files = None
        self.actions = None

    def tokenize(self):
        if self.commit:
            for token in self.commit.tokenize():
                yield token

    @staticmethod
    def parse(data):
        """Create an initialized CommitInfo object

        :param data: JSON representation of the revision as emitted by Gerrit
        :type data: str
        :rtype: CommitInfo
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
    """A change object"""

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
        yield Token.Generic.Heading, 'change-id %s' % self.change_id
        yield NEW_LINE

        yield Token.Text, 'Owner:   '
        for token in self.owner.tokenize():
            yield token

        yield NEW_LINE
        yield Token.Text, 'Subject: %s' % self.subject

    @staticmethod
    def parse(data):
        """Create an initialized ChangeInfo object

        :param data: JSON representation of the change as emitted by Gerrit
        :type data: str
        :rtype: ChangeInfo
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


class ReviewerInfo(Info):
    """A reviewer object"""

    def __init__(self):
        self.reviewer = None
        self.approvals = None

    def tokenize(self):
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
        """Create an initialized ReviewerInfo object

        :param data: JSON representation of the reviewer as emitted by Gerrit
        :type data: str
        :rtype: ReviewerInfo
        """

        reviewer = ReviewerInfo()

        reviewer.reviewer = AccountInfo.parse(data)
        reviewer.approvals = data['approvals'].items()

        return reviewer


class ReviewInfo(Info):
    """A review object"""

    def __init__(self):
        self.labels = None

    def tokenize(self):
        # In a ReviewInfo record, scores are numbers: we need to convert them
        # to string
        for label, score in self.labels:
            if score in (1, 2):
                token = Token.Review.OK
                score = '+%d' % score
            elif score in (-1, -2):
                token = Token.Review.KO
            else:
                token = Token.Review.NONE

            yield Token.Text, '    %s: ' % label
            yield token, str(score)
            yield NEW_LINE

    @staticmethod
    def parse(data):
        """Create an initialized ReviewInfo object

        :param data: JSON representation of the review as emitted by Gerrit
        :type data: str
        :rtype: ReviewInfo
        """

        review = ReviewInfo()
        review.labels = data['labels'].items()

        return review


class CapabilityInfo(Info):
    """A capability object"""

    def __init__(self):
        self.administrate_server = None
        self.query_limit = None
        self.create_account = None
        self.create_group = None
        self.create_project = None
        self.email_reviewers = None
        self.kill_task = None
        self.view_caches = None
        self.flush_caches = None
        self.view_connections = None
        self.view_queue = None
        self.run_gc = None

    def tokenize(self):
        pass  # ???(delay)

    @staticmethod
    def parse(data):
        """Create an initialized CapabilityInfo object

        :param data: JSON representation of the capability as emitted by Gerrit
        :type data: str
        :rtype: CapabilityInfo
        """

        capability = CapabilityInfo()
        capability.administrate_server = data.get('administrateServer', False)
        capability.query_limit = QueryLimitInfo.parse(data['queryLimit'])
        capability.create_account = data.get('createAccount', False)
        capability.create_group = data.get('createGroup', False)
        capability.create_project = data.get('createProject', False)
        capability.email_reviewers = data.get('emailReviewers', False)
        capability.kill_task = data.get('killTask', False)
        capability.view_caches = data.get('viewCaches', False)
        capability.flush_caches = data.get('flushCaches', False)
        capability.view_connections = data.get('viewConnections', False)
        capability.view_queue = data.get('viewQueue', False)
        capability.run_gc = data.get('runGC', False)

        return capability


class DiffPreferencesInfo(Info):
    """A diff preferences object"""

    def __init__(self):
        self.context = None
        self.expand_all_comments = None
        self.ignore_whitespaces = None
        self.intraline_difference = None
        self.line_length = None
        self.manual_review = None
        self.retain_header = None
        self.show_line_endings = None
        self.show_tabs = None
        self.show_whitespace_errors = None
        self.skip_deleted = None
        self.skip_uncommented = None
        self.syntax_highlighting = None
        self.tab_size = None

    def tokenize(self):
        pass  # ???(delay)

    @staticmethod
    def parse(data):
        """Create an initialized DiffPreferencesInfo object

        :param data: JSON representation of the review as emitted by Gerrit
        :type data: str
        :rtype: DiffPreferencesInfo
        """

        pref = DiffPreferencesInfo()
        pref.context = data['context']
        pref.expand_all_comments = data.get('expand_all_comments', False)
        pref.ignore_whitespaces = data['ignore_whitespaces']
        pref.intraline_difference = data.get('intraline_difference', False)
        pref.line_length = data['line_length']
        pref.manual_review = data.get('manual_review', False)
        pref.retain_header = data.get('retain_header', False)
        pref.show_line_endings = data.get('show_line_endings', False)
        pref.show_tabs = data.get('show_tabs', False)
        pref.show_whitespace_errors = data.get('show_whitespace_errors', False)
        pref.skip_deleted = data.get('skip_deleted', False)
        pref.skip_uncommented = data.get('skip_uncommented', False)
        pref.syntax_highlighting = data.get('syntax_highlighting', False)
        pref.tab_size = data['tab_size']

        return pref


class EmailInfo(Info):
    """An email info object"""

    def __init__(self):
        self.email = None
        self.preferred = None
        self.pending_confirmation = None

    def tokenize(self):
        pass  # ???(delay)

    @staticmethod
    def parse(data):
        """Create an initialized EmailInfo object

        :param data: JSON representation of the email as emitted by Gerrit
        :type data: str
        :rtype: EmailInfo
        """

        email = EmailInfo()
        email.email = data['email']
        email.preferred = data.get('preferred', False)
        email.pending_confirmation = data.get('pending_confirmation', False)

        return email


class QueryLimitInfo(Info):
    """A query limit info object"""

    def __init__(self):
        self.min = None
        self.max = None

    def tokenize(self):
        pass  # ???(delay)

    @staticmethod
    def parse(data):
        """Create an initialized QueryLimitInfo object

        :param data: JSON representation of the query limit as emitted by
            Gerrit
        :type data: str
        :rtype: QueryLimitInfo
        """

        limit = QueryLimitInfo()
        limit.min = int(data['min'])
        limit.max = int(data['max'])

        return limit


class SshKeyInfo(Info):
    """A SSH key info object"""

    def __init__(self):
        self.seq = None
        self.ssh_public_key = None
        self.encoded_key = None
        self.algorithm = None
        self.comment = None
        self.valid = None

    def tokenize(self):
        pass  # ???(delay)

    @staticmethod
    def parse(data):
        """Create an initialized SshKeyInfo object

        :param data: JSON representation of the ssh key as emitted by Gerrit
        :type data: str
        :rtype: SshKeyInfo
        """

        key = SshKeyInfo()
        key.seq = int(data['seq'])
        key.ssh_public_key = data['ssh_public_key']
        key.encoded_key = data['encoded_key']
        key.algorithm = data['algorithm']
        key.comment = data.get('comment', None)
        key.valid = data['valid']

        return key
