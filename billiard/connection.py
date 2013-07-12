from __future__ import absolute_import

import os
import sys

is_pypy = hasattr(sys, 'pypy_version_info')

if sys.version_info[0] == 3:
    from . import _connection3 as connection
else:
    from . import _connection as connection  # noqa


if is_pypy:
    import _multiprocessing
    from .compat import setblocking

    class Connection(_multiprocessing.Connection):

        def send_offset(self, buf, offset, write=os.write):
            return write(self.fileno(), buf[offset:])

        def setblocking(self, blocking):
            setblocking(self.fileno(), blocking)
    _multiprocessing.Connection = Connection


sys.modules[__name__] = connection
