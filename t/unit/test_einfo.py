import inspect
import logging
import pickle
import sys
import types

from billiard.einfo import _Code  # noqa
from billiard.einfo import _Frame  # noqa
from billiard.einfo import _Object  # noqa
from billiard.einfo import _Truncated  # noqa
from billiard.einfo import ExceptionInfo, Traceback

logger = logging.getLogger(__name__)


def test_exception_info_log_before_pickle(caplog):
    try:
        raise RuntimeError("some message")
    except Exception:
        exception = ExceptionInfo().exception

    logger.exception("failed", exc_info=exception)
    assert ' raise RuntimeError("some message")' in caplog.text
    assert "RuntimeError: some message" in caplog.text


def test_exception_info_log_after_pickle(caplog):
    try:
        raise RuntimeError("some message")
    except Exception:
        exception = ExceptionInfo().exception
        exception = pickle.loads(pickle.dumps(exception))

    logger.exception("failed", exc_info=exception)
    assert ' raise RuntimeError("some message")' in caplog.text
    assert "RuntimeError: some message" in caplog.text


def test_exception_info():
    try:
        raise ValueError("Test Exception")
    except ValueError:
        exc_info = sys.exc_info()
        e_info = ExceptionInfo(exc_info)
        assert isinstance(e_info.type, type)
        assert isinstance(e_info.exception, Exception)
        assert isinstance(e_info.tb, Traceback)
        assert isinstance(e_info.traceback, str)


def test_traceback():
    try:
        raise ValueError("Test Exception")
    except ValueError:
        tb = sys.exc_info()[2]
        trace = Traceback(tb)
        assert isinstance(trace.tb_frame, _Frame)
        assert isinstance(trace.tb_lineno, int)
        assert isinstance(trace.tb_lasti, int)
        assert trace.tb_next is None or isinstance(trace.tb_next, Traceback)


def test_frame():
    try:
        raise ValueError("Test Exception")
    except ValueError:
        tb = sys.exc_info()[2]
        frame = _Frame(tb.tb_frame)
        assert isinstance(frame.f_code, _Code)
        assert isinstance(frame.f_lineno, int)
        assert isinstance(frame.f_lasti, int)
        assert frame.f_globals == {
            "__file__": frame.f_globals.get("__file__", "__main__"),
            "__name__": frame.f_globals.get("__name__"),
            "__loader__": None,
        }


def test_code():
    try:
        raise ValueError("Test Exception")
    except ValueError:
        tb = sys.exc_info()[2]
        frame = tb.tb_frame
        code = _Code(frame.f_code)
        assert isinstance(code.co_filename, str)
        assert isinstance(code.co_name, str)
        assert isinstance(code.co_argcount, int)
        if sys.version_info >= (3, 11):
            assert callable(code.co_positions)
            assert next(code.co_positions()) == (79, 79, 0, 0)


def test_object_init():
    obj = _Object(a=1, b=2, c=3)
    assert obj.a == 1
    assert obj.b == 2
    assert obj.c == 3


if sys.version_info >= (3, 11):

    def test_object_co_positions():
        obj = _Object()

        default = ((None, None, None, None),)
        # Test that it returns the default co_positions
        assert list(iter(obj.co_positions())) == list(default)

        # Test setting co_positions
        new_value = ((1, 2, 3, 4),)
        obj.co_positions = new_value
        assert list(iter(obj.co_positions())) == list(new_value)

    def test_truncated_co_positions():
        truncated = _Truncated()

        assert list(iter(truncated.co_positions())) == list(
            iter(truncated.tb_frame.co_positions())
        )


def make_python_tb():
    tb = None
    depth = 0
    while True:
        try:
            frame = sys._getframe(depth)
        except ValueError:
            break
        else:
            depth += 1

        tb = types.TracebackType(tb, frame, frame.f_lasti, frame.f_lineno)

    assert tb is not None, "Failed to create a traceback object"

    return tb


def test_isinstance():
    tb = Traceback(tb=make_python_tb())
    frame = tb.tb_frame
    code = frame.f_code

    assert isinstance(tb, types.TracebackType)
    assert isinstance(tb, Traceback)
    assert isinstance(frame, types.FrameType)
    assert isinstance(frame, _Frame)
    assert isinstance(code, types.CodeType)
    assert isinstance(code, _Code)


def repickle(obj):
    """Round-trip an object through pickle."""
    return pickle.loads(pickle.dumps(obj))


def test_pickle():
    """
    While `__class__` is overridden to return the built-in types,
    this would break unpickling in Python versions prior to 3.10
    """
    tb = Traceback(tb=make_python_tb())
    tb2 = repickle(tb)

    assert type(tb2) == type(tb)
    assert tb2.tb_lineno == tb.tb_lineno

    frame = tb.tb_frame
    frame2 = repickle(frame)

    assert type(frame2) == type(frame)
    assert frame2.f_lineno == frame.f_lineno

    code = frame.f_code
    code2 = repickle(code)

    assert type(code2) == type(code)
    assert code2.co_name == code.co_name


class TestInspect:
    def test_istraceback(self):
        tb = Traceback(tb=make_python_tb())
        assert inspect.istraceback(tb)
        assert inspect.istraceback(repickle(tb))

    def test_isframe(self):
        frame = _Frame(make_python_tb().tb_frame)
        assert inspect.isframe(frame)
        assert inspect.isframe(repickle(frame))

    def test_iscode(self):
        code = _Code(make_python_tb().tb_frame.f_code)
        assert inspect.iscode(code)
        assert inspect.iscode(repickle(code))

    def test_getframeinfo(self):
        tb = Traceback(make_python_tb())
        assert inspect.getframeinfo(tb)
        assert inspect.getframeinfo(repickle(tb))

        frame = tb.tb_frame
        assert inspect.getframeinfo(frame)
        assert inspect.getframeinfo(repickle(frame))

    def test_getinnerframes(self):
        tb = Traceback(tb=make_python_tb())
        assert inspect.getinnerframes(tb)
        assert inspect.getinnerframes(repickle(tb))
