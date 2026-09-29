import time

import pytest

from billiard import Process


class test_Process:

    def test_close_while_running_raises(self):
        # close() used to close the sentinel of a live child, after which
        # join() failed with a TypeError and the child was never reaped.
        p = Process(target=time.sleep, args=(0.5,))
        p.start()
        try:
            with pytest.raises(ValueError, match='still running'):
                p.close()
        finally:
            p.join(5)
        assert p.exitcode == 0
        p.close()
