from __future__ import absolute_import

import errno
import os

try:
    bytes = bytes
except NameError:
    def bytes(s, encoding='ascii'):  # noqa
        return str(s).encode(encoding)


try:
    closerange = os.closerange
except AttributeError:

    def closerange(fd_low, fd_high):  # noqa
        for fd in reversed(xrange(fd_low, fd_high)):
            try:
                os.close(fd)
            except OSError, exc:
                if exc.errno != errno.EBADF:
                    raise
