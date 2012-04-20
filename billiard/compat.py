import errno
import os
import sys

try:
    bytes = bytes
except NameError:
    bytes = str  # noqa


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
