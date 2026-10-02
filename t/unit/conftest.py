import pytest

from billiard import common


@pytest.fixture(autouse=True)
def reset_terminate_handler_fired():
    """Keep ``common._should_have_exited`` from leaking between tests.

    The flag is a module global, and any test that calls ``_shutdown_cleanup``
    in the test process -- ``test_common.test_shutdown_handler`` does, with
    ``sys.exit`` patched out -- leaves it True for the rest of the session.
    Nothing resets it in-process, so a later test exercising the workloop
    would silently take the shutdown branch and pass or fail for a reason
    that has nothing to do with what it is testing.
    """
    previous = common._should_have_exited[0]
    try:
        yield
    finally:
        common._should_have_exited[0] = previous
