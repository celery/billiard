"""Python multiprocessing fork"""

from __future__ import absolute_import

VERSION = (2, 7, 3, 0)
__version__ = ".".join(map(str, VERSION[0:4])) + "".join(VERSION[4:])
__author__ = 'R Oudkerk / Python Software Foundation'
__author_email__ = 'python-dev@python.org'
__maintainer__ = 'Ask Solem',
__contact__ = "ask@celeryproject.org"
__homepage__ = "http://github.com/ask/billiard"
__docformat__ = "restructuredtext"

# -eof meta-


#
# Package analogous to 'threading.py' but using processes
#
# billiard/__init__.py
#
# This package is intended to duplicate the functionality (and much of
# the API) of threading.py but uses processes instead of threads.  A
# subpackage 'billiard.dummy' has the same API but is a simple
# wrapper for 'threading'.
#
# Try calling `billiard.doc.main()` to read the html
# documentation in in a webbrowser.
#
#
# Copyright (c) 2006-2008, R Oudkerk
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of author nor the names of any contributors may be
#    used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#

__all__ = [
    'Process', 'current_process', 'active_children', 'freeze_support',
    'Manager', 'Pipe', 'cpu_count', 'log_to_stderr', 'get_logger',
    'allow_connection_pickling', 'BufferTooShort', 'TimeoutError',
    'Lock', 'RLock', 'Semaphore', 'BoundedSemaphore', 'Condition',
    'Event', 'Queue', 'JoinableQueue', 'Pool', 'Value', 'Array',
    'RawValue', 'RawArray', 'SUBDEBUG', 'SUBWARNING', 'set_executable',
    'forking_enable', 'forking_is_enabled'
    ]

#
# Imports
#

import os
import sys

from .process import Process, current_process, active_children
from .util import SUBDEBUG, SUBWARNING

#
# Exceptions
#

class ProcessError(Exception):
    pass

class BufferTooShort(ProcessError):
    pass

class TimeoutError(ProcessError):
    pass

class AuthenticationError(ProcessError):
    pass

# This is down here because _billiard uses BufferTooShort
import _billiard

#
# Definitions not depending on native semaphores
#

def Manager():
    '''
    Returns a manager associated with a running server process

    The managers methods such as `Lock()`, `Condition()` and `Queue()`
    can be used to create shared objects.
    '''
    from .managers import SyncManager
    m = SyncManager()
    m.start()
    return m

def Pipe(duplex=True):
    '''
    Returns two connection object connected by a pipe
    '''
    from .connection import Pipe
    return Pipe(duplex)

def cpu_count():
    '''
    Returns the number of CPUs in the system
    '''
    if sys.platform == 'win32':
        try:
            num = int(os.environ['NUMBER_OF_PROCESSORS'])
        except (ValueError, KeyError):
            num = 0
    elif 'bsd' in sys.platform or sys.platform == 'darwin':
        try:
            num = int(os.popen('sysctl -n hw.ncpu').read())
        except ValueError:
            num = 0
    else:
        try:
            num = os.sysconf('SC_NPROCESSORS_ONLN')
        except (ValueError, OSError, AttributeError):
            num = 0

    if num >= 1:
        return num
    else:
        raise NotImplementedError('cannot determine number of cpus')

def freeze_support():
    '''
    Check whether this is a fake forked process in a frozen executable.
    If so then run code specified by commandline and exit.
    '''
    if sys.platform == 'win32' and getattr(sys, 'frozen', False):
        from .forking import freeze_support
        freeze_support()

def get_logger():
    '''
    Return package logger -- if it does not already exist then it is created
    '''
    from .util import get_logger
    return get_logger()

def log_to_stderr(level=None):
    '''
    Turn on logging and add a handler which prints to stderr
    '''
    from .util import log_to_stderr
    return log_to_stderr(level)

def allow_connection_pickling():
    '''
    Install support for sending connections and sockets between processes
    '''
    from . import reduction

#
# Definitions depending on native semaphores
#

def Lock():
    '''
    Returns a non-recursive lock object
    '''
    from .synchronize import Lock
    return Lock()

def RLock():
    '''
    Returns a recursive lock object
    '''
    from .synchronize import RLock
    return RLock()

def Condition(lock=None):
    '''
    Returns a condition object
    '''
    from .synchronize import Condition
    return Condition(lock)

def Semaphore(value=1):
    '''
    Returns a semaphore object
    '''
    from .synchronize import Semaphore
    return Semaphore(value)

def BoundedSemaphore(value=1):
    '''
    Returns a bounded semaphore object
    '''
    from .synchronize import BoundedSemaphore
    return BoundedSemaphore(value)

def Event():
    '''
    Returns an event object
    '''
    from .synchronize import Event
    return Event()

def Queue(maxsize=0):
    '''
    Returns a queue object
    '''
    from .queues import Queue
    return Queue(maxsize)

def JoinableQueue(maxsize=0):
    '''
    Returns a queue object
    '''
    from .queues import JoinableQueue
    return JoinableQueue(maxsize)

def Pool(processes=None, initializer=None, initargs=(), maxtasksperchild=None):
    '''
    Returns a process pool object
    '''
    from .pool import Pool
    return Pool(processes, initializer, initargs, maxtasksperchild)

def RawValue(typecode_or_type, *args):
    '''
    Returns a shared object
    '''
    from .sharedctypes import RawValue
    return RawValue(typecode_or_type, *args)

def RawArray(typecode_or_type, size_or_initializer):
    '''
    Returns a shared array
    '''
    from .sharedctypes import RawArray
    return RawArray(typecode_or_type, size_or_initializer)

def Value(typecode_or_type, *args, **kwds):
    '''
    Returns a synchronized shared object
    '''
    from .sharedctypes import Value
    return Value(typecode_or_type, *args, **kwds)

def Array(typecode_or_type, size_or_initializer, **kwds):
    '''
    Returns a synchronized shared array
    '''
    from .sharedctypes import Array
    return Array(typecode_or_type, size_or_initializer, **kwds)

#
#
#

def set_executable(executable):
    '''
    Sets the path to a python.exe or pythonw.exe binary used to run
    child processes on Windows instead of sys.executable.
    Useful for people embedding Python.
    '''
    from .forking import set_executable
    set_executable(executable)

def forking_is_enabled():
    '''
    Returns a boolean value indicating whether billiard is
    currently set to create child processes by forking the current
    python process rather than by starting a new instances of python.

    On Windows this always returns `False`.  On Unix it returns `True` by
    default.
    '''
    from . import forking
    return forking._forking_is_enabled

def forking_enable(value):
    '''
    Enable/disable creation of child process by forking the current process.

    `value` should be a boolean value.  If `value` is true then
    forking is enabled.  If `value` is false then forking is disabled.
    On systems with `os.fork()` forking is enabled by default, and on
    other systems it is always disabled.
    '''
    from . import forking
    if value and not hasattr(os, 'fork'):
        raise ValueError('os.fork() not found')
    forking._forking_is_enabled = bool(value)
