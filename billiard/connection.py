from __future__ import absolute_import


import sys

if sys.version_info[0] == 3:
    from multiprocessing.connection import *  # noqa
else:
    from ._connection import *                # noqa
