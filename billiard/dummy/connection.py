import sys

if sys.version_info[0] == 3:
    from ..py3.dummy import connection
else:
    from ..py2.dummy import connection  # noqa