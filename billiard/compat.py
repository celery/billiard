from __future__ import absolute_import

import errno
import os
import sys

from .five import builtins, range

try:
    import _winapi
except ImportError:                            # pragma: no cover
    try:
        from billiard import win32 as _winapi  # noqa
    except (ImportError, AttributeError):
        _winapi = None                         # noqa

if sys.version_info[0] == 3:
    bytes = bytes
else:
    try:
        _bytes = builtins.bytes
    except AttributeError:
        _bytes = str

    class bytes(_bytes):  # noqa

        def __new__(cls, *args):
            if len(args) > 1:
                return _bytes(args[0]).encode(*args[1:])
            return _bytes(*args)

try:
    closerange = os.closerange
except AttributeError:

    def closerange(fd_low, fd_high):  # noqa
        for fd in reversed(range(fd_low, fd_high)):
            try:
                os.close(fd)
            except OSError as exc:
                if exc.errno != errno.EBADF:
                    raise


def get_errno(exc):
    """:exc:`socket.error` and :exc:`IOError` first got
    the ``.errno`` attribute in Py2.7"""
    try:
        return exc.errno
    except AttributeError:
        try:
            # e.args = (errno, reason)
            if isinstance(exc.args, tuple) and len(exc.args) == 2:
                return exc.args[0]
        except AttributeError:
            pass
    return 0


if _winapi:

    def setblocking(handle, blocking):
        raise NotImplementedError('setblocking not implemented on win32')

else:
    from os import O_NONBLOCK
    from fcntl import fcntl, F_GETFL, F_SETFL

    def setblocking(handle, blocking):  # noqa
        flags = fcntl(handle, F_GETFL, 0)
        if flags > 0:
            fcntl(
                handle, F_SETFL,
                flags & (~O_NONBLOCK) if blocking else flags | O_NONBLOCK,
            )
