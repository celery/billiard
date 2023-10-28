import logging
import pickle
import sys

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
            assert next(code.co_positions()) == (77, 77, 0, 0)


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
