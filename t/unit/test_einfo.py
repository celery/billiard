import pickle
import logging
from billiard.einfo import ExceptionInfo

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
