"""
This module encapsulate the logic for querying an HTTP server.
"""

import getpass
import logging
import json
import requests

from libpycr.exceptions import RequestError
from libpycr.utils.system import fail

from requests.auth import HTTPDigestAuth
from requests.exceptions import ConnectionError, RequestException

from urlparse import urlparse


class RequestFactory(object):
    """A Request factory."""

    # Logger
    log = logging.getLogger(__name__)

    # Remote
    host = None

    # Credentials
    username = None
    password = None

    # Connection
    unsecure = False

    # HTTP protocol method supported by this application
    GET = ('GET', requests.get)
    POST = ('POST', requests.post)
    DELETE = ('DELETE', requests.delete)

    # To prevent against Cross Site Script Inclusion (XSSI) attacks, the JSON
    # response body starts with a magic prefix line that must be stripped
    GERRIT_MAGIC = ")]}'\n"

    @classmethod
    def set_auth_token(cls, username, password=None):
        """
        Set the authentication pair to use for HTTP requests.

        PARAMETERS
            username: the account username
            password: the account HTTP password
        """

        cls.username = username
        cls.password = password

    @classmethod
    def require_auth(cls):
        """
        Return True if authentication is required.
        Check whether cls.username is None.

        RETURNS
            True if auth required, False otherwise
        """

        return cls.username is not None

    @classmethod
    def get_http_digest_auth_token(cls):
        """
        Return the HTTPDigestAuth object to use for authentication.
        Prompt the user if the password is unknown.

        RETURNS
            requests.auth.HTTPDigestAuth
        """

        if cls.password is None:
            cls.password = getpass.getpass()

        return HTTPDigestAuth(cls.username, cls.password)

    @classmethod
    def set_host(cls, host):
        """Set the Gerrit Code Review server host name.

        PARAMETERS
            host: the server's host
        """

        cls.host = host

    @classmethod
    def set_unsecure_connection(cls, unsecure):
        """If True, requests will be made over HTTP instead of HTTPS.

        Always use HTTPS by default.

        PARAMETERS
            unsecure: True to use HTTP
        """

        cls.unsecure = unsecure

    @classmethod
    def get_remote_base_url(cls):
        """
        Return the Gerrit Code Review server base URL.

        RETURNS
            the Gerrit Code Review server base URL as a string
        """

        if cls.host is None:
            fail('gerrit.host not set')

        url = cls.host

        # From Gerrit Code Review Documentation (section Authentication):
        # https://gerrit-review.googlesource.com/Documentation/rest-api.html
        #
        # Users (and programs) may authenticate using HTTP authentication by
        # supplying the HTTP password from the user's account settings page.
        # Gerrit by default uses HTTP digest authentication. To authenticate,
        # prefix the endpoint URL with /a/. For example to authenticate to
        # /projects/ request URL /a/projects/.

        if RequestFactory.require_auth():
            url = '%s/a' % url

        if not url.startswith('http://') or not url.startswith('https://'):
            return '%s://%s' % ('http' if cls.unsecure else 'https', url)

        return url

    @classmethod
    def send(cls, endpoint, method=GET, **kwargs):
        """
        Return the result of a HTTP request.

        PARAMETERS
            endpoint: the endpoint to the request
            method: HTTP protocol method to use (either RequestFactory.GET or
                RequestFactory.POST)
            **kwargs: any additional arguments to the underlying API call

        RETURNS
            a tuple of two elements: the raw response (stripped from magic) and
                the json object of that response, or None if no content (status
                code 204)

        RAISES
            requests.exceptions.RequestException on error
        """

        cls.log.debug('Query URL: %s' % endpoint)

        name, callback = method
        headers = kwargs['headers'] if 'headers' in kwargs else {}

        if 'auth' in kwargs.keys() or cls.username is None:
            return callback(endpoint, **kwargs)

        if cls.password is None:
            cls.password = getpass.getpass()

        try:
            kwargs['auth'] = RequestFactory.get_http_digest_auth_token()
            kwargs['headers'] = headers

            response = callback(endpoint, **kwargs)

            if response.status_code == 204:
                # No content
                return None, None

            if response.status_code != 200:
                response.raise_for_status()

        except ConnectionError as why:
            fail('Unable to connect to %s' % urlparse(endpoint).netloc)

        except RequestException as why:
            raise RequestError(
                response.status_code,
                'HTTP %s request failed: %s' % (name, endpoint), why)

        if not response.text.startswith(RequestFactory.GERRIT_MAGIC):
            fail('invalid Gerrit Code Review stream (magic prefix not found)')

        return (response.text,
                json.loads(response.text[len(RequestFactory.GERRIT_MAGIC):]))

    @classmethod
    def get(cls, endpoint, **kwargs):
        """
        Return the result of a HTTP GET request.

        PARAMETERS
            endpoint: the endpoint to GET
            **kwargs: any additional arguments to the underlying GET call

        RETURNS
            a tuple of two elements: the raw response (stripped from magic) and
                the json object of that response

        RAISES
            requests.exceptions.RequestException on error
        """

        return cls.send(endpoint, method=RequestFactory.GET, **kwargs)

    @classmethod
    def post(cls, endpoint, **kwargs):
        """
        Return the result of a HTTP POST request.

        PARAMETERS
            endpoint: the endpoint to POST
            **kwargs: any additional arguments to the underlying POST call

        RETURNS
            a tuple of two elements: the raw response (stripped from magic) and
                the json object of that response

        RAISES
            requests.exceptions.RequestException on error
        """

        return cls.send(endpoint, method=RequestFactory.POST, **kwargs)

    @classmethod
    def delete(cls, endpoint, **kwargs):
        """
        Return the result of a HTTP DELETE request.

        PARAMETERS
            endpoint: the endpoint to DELETE
            **kwargs: any additional arguments to the underlying DELETE call

        RAISES
            requests.exceptions.RequestException on error
        """

        cls.send(endpoint, method=RequestFactory.DELETE, **kwargs)
