import sys
import pickle
import logging
import inspect
import types
from billiard.einfo import ExceptionInfo, Traceback, _Code, _Frame

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

    return tb


class test_inspect:
    def test_istraceback(self):
        assert inspect.istraceback(Traceback(tb=make_python_tb()))

    def test_isframe(self):
        assert inspect.isframe(_Frame(make_python_tb().tb_frame))

    def test_iscode(self):
        assert inspect.iscode(_Code(make_python_tb().tb_frame.f_code))

    def test_getframeinfo(self):
        assert inspect.getframeinfo(Traceback(tb=make_python_tb()))

    def test_getinnerframes(self):
        assert inspect.getinnerframes(Traceback(tb=make_python_tb()))
