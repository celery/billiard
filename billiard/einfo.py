from __future__ import absolute_import

import sys
import traceback
from copy import copy
from types import CodeType
from types import TracebackType

from .five import PY3
from .five import reraise

def __make_tb_set_next():
    """This function implements a few ugly things so that we can patch the
    traceback objects.  The function returned allows resetting `tb_next` on
    any python traceback object.  Do not attempt to use this on non cpython
    interpreters
    """
    import ctypes

    # figure out side of _Py_ssize_t
    if hasattr(ctypes.pythonapi, 'Py_InitModule4_64'):
        _Py_ssize_t = ctypes.c_int64
    else:
        _Py_ssize_t = ctypes.c_int

    # regular python
    class _PyObject(ctypes.Structure):
        pass
    _PyObject._fields_ = [
        ('ob_refcnt', _Py_ssize_t),
        ('ob_type', ctypes.POINTER(_PyObject))
    ]

    # python with trace
    if hasattr(sys, 'getobjects'):
        class _PyObject(ctypes.Structure):
            pass
        _PyObject._fields_ = [
            ('_ob_next', ctypes.POINTER(_PyObject)),
            ('_ob_prev', ctypes.POINTER(_PyObject)),
            ('ob_refcnt', _Py_ssize_t),
            ('ob_type', ctypes.POINTER(_PyObject))
        ]

    class _Traceback(_PyObject):
        pass
    _Traceback._fields_ = [
        ('tb_next', ctypes.POINTER(_Traceback)),
        ('tb_frame', ctypes.POINTER(_PyObject)),
        ('tb_lasti', ctypes.c_int),
        ('tb_lineno', ctypes.c_int)
    ]

    def tb_set_next(tb, next):
        """Set the tb_next attribute of a traceback object."""
        if not (isinstance(tb, TracebackType) and
                (next is None or isinstance(next, TracebackType))):
            raise TypeError('tb_set_next arguments must be traceback objects')
        obj = _Traceback.from_address(id(tb))
        if tb.tb_next is not None:
            old = _Traceback.from_address(id(tb.tb_next))
            old.ob_refcnt -= 1
        if next is None:
            obj.tb_next = ctypes.POINTER(_Traceback)()
        else:
            next = _Traceback.from_address(id(next))
            next.ob_refcnt += 1
            obj.tb_next = ctypes.pointer(next)

    return tb_set_next

_tb_set_next = _tproxy = None
try:
    from __pypy__ import tproxy as _tproxy
except ImportError:
    try:
        _tb_set_next = __make_tb_set_next()
    except Exception:
        pass

class __traceback_maker(Exception):
    pass

class _Code(object):

    def __init__(self, code):
        self.co_filename = code.co_filename
        self.co_name = code.co_name
        self.co_nlocals = code.co_nlocals
        self.co_stacksize = code.co_stacksize
        self.co_flags = code.co_flags
        self.co_firstlineno = code.co_firstlineno
        self.co_lnotab = code.co_lnotab

class _Frame(object):
    Code = _Code

    def __init__(self, frame):
        self.f_globals = {
            "__file__": frame.f_globals.get("__file__", "__main__"),
            "__name__": frame.f_globals.get("__name__"),
            "__loader__": None,
        }
        self.f_locals = fl = {}
        try:
            fl["__traceback_hide__"] = frame.f_locals["__traceback_hide__"]
        except KeyError:
            pass
        self.f_code = self.Code(frame.f_code)
        self.f_lineno = frame.f_lineno


class _Object(object):

    def __init__(self, **kw):
        [setattr(self, k, v) for k, v in kw.items()]


class _Truncated(object):

    def __init__(self):
        self.tb_lineno = -1
        self.tb_frame = _Object(
            f_globals={"__file__": "",
                       "__name__": "",
                       "__loader__": None},
            f_fileno=None,
            f_code=_Object(co_filename="...",
                           co_name="[rest of traceback truncated]"),
        )
        self.tb_next = None


class Traceback(object):
    Frame = _Frame

    tb_frame = tb_lineno = tb_next = None
    max_frames = sys.getrecursionlimit() // 8

    def __init__(self, tb, max_frames=None, depth=0):
        limit = self.max_frames = max_frames or self.max_frames
        self.tb_frame = self.Frame(tb.tb_frame)
        self.tb_lineno = tb.tb_lineno
        if tb.tb_next is not None:
            if depth <= limit:
                self.tb_next = Traceback(tb.tb_next, limit, depth + 1)
            else:
                self.tb_next = _Truncated()

    def as_traceback(self):
        """
        Returns Traceback instance that is adequate for raising or None if there's no support in the python runtime.
        """
        try:
            # perform few sanity checks, in case the objects are incomplete (eg: older billiard)
            f_code = self.tb_frame.f_code
            f_code.co_nlocals
            f_code.co_stacksize
            f_code.co_flags
            f_code.co_firstlineno
            f_code.co_lnotab
        except AttributeError:
            return
        if _tproxy:
            return _tproxy(TracebackType, self.__tproxy_handler)
        elif _tb_set_next:
            code = compile('\n' * (self.tb_lineno - 1) + 'raise __traceback_maker', self.tb_frame.f_code.co_filename, 'exec')
            if PY3:
                code = CodeType(
                    0, 0,
                    f_code.co_nlocals, f_code.co_stacksize, f_code.co_flags,
                    code.co_code, code.co_consts, code.co_names, code.co_varnames,
                    f_code.co_filename, f_code.co_name,
                    code.co_firstlineno, code.co_lnotab,
                    (), ()
                )
            else:
                code = CodeType(
                    0,
                    f_code.co_nlocals, f_code.co_stacksize, f_code.co_flags,
                    code.co_code, code.co_consts, code.co_names, code.co_varnames,
                    f_code.co_filename, f_code.co_name,
                    code.co_firstlineno, code.co_lnotab,
                    (), ()
                )

            try:
                exec(code, self.tb_frame.f_globals, {})
            except:
                tb = sys.exc_info()[2].tb_next
                _tb_set_next(tb, self.tb_next and self.tb_next.as_traceback())
                return tb
        else:
            return None

    def __tproxy_handler(self, operation, *args, **kwargs):
        if operation in ('__getattribute__', '__getattr__'):
            if args[0] == 'tb_next':
                return self.tb_next and self.tb_next.as_traceback()
            else:
                return getattr(self, args[0])
        else:
            return getattr(self, operation)(*args, **kwargs)

class ExceptionInfo(object):
    """Exception wrapping an exception and its traceback.

    :param exc_info: The exception info tuple as returned by
        :func:`sys.exc_info`.

    """

    #: Exception type.
    type = None

    #: Exception instance.
    exception = None

    #: Pickleable traceback instance for use with :mod:`traceback`
    tb = None

    #: String representation of the traceback.
    traceback = None

    #: Set to true if this is an internal error.
    internal = False

    def __init__(self, exc_info=None, internal=False):
        self.type, self.exception, tb = exc_info or sys.exc_info()
        try:
            self.tb = Traceback(tb)
            self.traceback = ''.join(
                traceback.format_exception(self.type, self.exception, tb),
            )
            self.internal = internal
        finally:
            del(tb)

    def __str__(self):
        return self.traceback

    def __repr__(self):
        return "<%s: %r>" % (self.__class__.__name__, self.exception, )

    @property
    def exc_info(self):
        return self.type, self.exception, self.tb

    def raise_(self):
        tb = self.tb.as_traceback()
        if PY3:
            exc = copy(self.exception)
            cause = exc.__cause__ = self.exception
            cause.__traceback__ = tb
            raise exc
        else:
            reraise(self.type, self.exception, tb)
