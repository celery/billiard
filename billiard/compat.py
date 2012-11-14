from __future__ import absolute_import

import errno
import os
import sys

from .five import builtins, range

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
