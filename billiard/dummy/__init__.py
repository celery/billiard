#!/usr/bin/env python
# coding: utf-8
from __future__ import absolute_import
import sys

if sys.version_info[0] == 3:
    from ..py3 import dummy
else:
    from ..py2 import dummy


sys.modules[__name__] = dummy