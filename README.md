PyCR
====

A Command-Line Interface to Gerrit Code Review v2.8 up to v2.11.4.

Quick start
-----------

Create a file named `~/.gitreview` with the following content:

     [gerrit]
     username = <your username>
     password = <http-password>
     host = <review hostname>

Where `<http-password>` is your HTTP access password for your account in Gerrit
(Settings > HTTP Password).

Then run:

     $ git cl list

to see the list of pending changes.

With `git-cl` you can review, submit or rebase a change. See `git cl -h` for
more info.
