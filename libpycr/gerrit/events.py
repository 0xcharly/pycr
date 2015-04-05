"""Gerrit Code Review event notifications"""

import collections
import json
import logging
import socket

import libpycr.gerrit.ssh

from libpycr.exceptions import PyCRError
from paramiko import AutoAddPolicy, SSHClient
from select import select


# Event separator charactor
EVENT_SEPARATOR = '\n'


class EventNotifier(object):
    """Connect to Gerrit events stream and notify on new events"""

    # Logger
    log = logging.getLogger(__name__)

    def __init__(self, host, port=libpycr.gerrit.ssh.PORT, username=None,
                 keyfile=None, passphrase=None):
        # Credentials to connect to the remote Gerrit server. Authentication is
        # handled via public/private key pair. Authentication via password is
        # not supported by the remote end.
        self._host = host
        self._port = port
        self._username = username
        self._keyfile = keyfile
        self._passphrase = passphrase

        # The SSH client that will connect to Gerrit
        self._ssh_client = None
        # Associate a list of callback for each event type
        self._event_listeners = collections.defaultdict(lambda: [])
        # List of "global" listeners, ie. callback invoked for each event
        self._global_listeners = []

        # Control socket used to cleanly exit from the blocking select() call
        # used to wait for input from the Gerrit server. This is used by the
        # stop() method in a multi-threaded environment.
        self._ctl_sock = None

    def set_ssh_username(self, username):
        """Username setter

        Call this method prior to :meth:`start`.

        :param username: the username to use to connect to Gerrit
        :type username: str
        """
        self._username = username

    def set_ssh_private_key(self, keyfile, passphrase=None):
        """SSH authentication via public/private key pair setter

        Call this method prior to :meth:`start`.

        :param keyfile: path to the key file
        :type keyfile: str
        :param passphrase: optional passphrase to unlock the encrypted keyfile
        :type passphrase: str | None
        """
        self._keyfile = keyfile
        self._passphrase = passphrase

    def listen(self, event_type, callback):
        """Register a callback on ``event_type``

        Call this method prior to :meth:`start`.

        :param event_type: the kind of event to listen to
        :type event_type: str
        :param callback: the routine to call when receiving a new event of kind
            ``event_type``. The callback takes one parameter: the event object.
        """
        self._event_listeners[event_type].append(callback)

    def listen_all(self, callback):
        """Register a callback on all events

        Call this method prior to :meth:`start`.

        :param callback: the routine to call when receiving any event kind.
            The callback takes one parameter: the event object.
        """
        self._global_listeners.append(callback)

    @staticmethod
    def _create_ctl_sock():
        """Helper function to create the control socket

        Binds the socket to localhost. The only purpose of this socket is to
        act as a control object to exit from a blocking select() call. It is
        not used to transmit any other kind of information.

        :return: the control socket
        :rtype: socket.socket
        """
        ctl_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ctl_sock.setblocking(0)
        ctl_sock.bind(('localhost', 0))  # Bind to any free port
        return ctl_sock

    def start(self):
        """Start the mainloop

        Connect to the remote Gerrit server and start listening for events,
        firing registered callbacks as events come.

        :raise PyCRError: if the mainloop is already running
        """
        # Control socket bound to localhost used to cleanly exit from the
        # blocking select() operation.
        if self._ctl_sock is not None:
            raise PyCRError('event notifier already running')
        self._ctl_sock = self._create_ctl_sock()

        kwargs = {
            'hostname': self._host,
            'port': self._port,
            'username': self._username
        }

        if self._keyfile is None:
            kwargs.update({'look_for_keys': True})
        else:
            kwargs.update({
                'keyfile': self._keyfile,
                'password': self._passphrase
            })

        self._ssh_client = SSHClient()
        self._ssh_client.load_system_host_keys()
        self._ssh_client.set_missing_host_key_policy(AutoAddPolicy())

        try:
            self._ssh_client.connect(**kwargs)
            channel = self._ssh_client.get_transport().open_session()
            channel.exec_command('gerrit stream-events')

            # Stream buffer to store bytes read from the SSH connection stream
            stream = ''

            while True:
                if channel.exit_status_ready():
                    break

                # Block on the SSH channel (waiting for event) and on the
                # control socket (waiting for a notification to exit the loop).
                readable, _, _ = select([channel, self._ctl_sock], [], [])

                if not len(readable):
                    # select() returned for another reason than a read-ready
                    # FD: ignore.
                    # ??? Handle "exceptional" conditions?
                    continue

                if self._ctl_sock in readable:
                    # The control socket triggered select(): cleanly close the
                    # SSH connection.
                    break

                # Read and process new event data available in 'channel'
                stream += channel.recv(libpycr.gerrit.ssh.RECV_BUFFER_SIZE)

                while EVENT_SEPARATOR in stream:
                    # Found a complete event in the stream; process it
                    event, _, stream = stream.partition(EVENT_SEPARATOR)
                    self._dispatch(json.loads(event))

        finally:
            self._ctl_sock.close()
            self._ssh_client.close()
            self._ssh_client = self._ctl_sock = None

    def stop(self):
        """Stop the mainloop

        If running, cleanly exits the select() call from the mainloop.

        :raise PyCRError: if the mainloop is not running
        """
        if not self._ctl_sock:
            raise PyCRError('event loop not listening')

        # Send a single byte through the control socket to trigger the select()
        # call and exit.
        self._ctl_sock.send('\x43')

    def _dispatch(self, event):
        """Dispatch an event and call all listeners for events of this type

        The type of the event is decided by the ``type`` property on the event
        object.

        :param event: the event object (ie. mapped JSON object)
        :type event: dict
        """
        if 'type' not in event:
            self.log.warn('ignoring event: missing field "type"')
            self.log.debug(event)
            return

        event_type = event['type']

        if event_type in self._event_listeners:
            for listener in self._event_listeners[event_type]:
                listener(event)

        for listener in self._global_listeners:
            listener(event)
