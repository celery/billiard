#!/usr/bin/env python
# coding: utf-8
import sys

if sys.version_info[0] == 3:
    from billiard.py3.dummy.connection import *
else:
    from billiard.py2.dummy.connection import *