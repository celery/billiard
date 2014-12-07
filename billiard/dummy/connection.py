#!/usr/bin/env python
# coding: utf-8
from __future__ import absolute_import
import sys

if sys.version_info[0] == 3:
    from ..py3.dummy import connection
else:
    from ..py2.dummy import connection

sys.modules[__name__] = connection