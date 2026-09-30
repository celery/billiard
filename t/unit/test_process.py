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

    def test_join_keeps_the_process_usable(self):
        # join() releases the sentinel itself, but the pool still reads
        # exitcode and pid afterwards, so it must not close the object.
        p = Process(target=time.sleep, args=(0,))
        p.start()
        p.join(5)
        assert p.exitcode == 0
        assert p.pid is not None
        assert not p.is_alive()

    def test_closed_process(self):
        p = Process(target=time.sleep, args=(0,))
        p.start()
        p.join(5)
        p.close()
        assert 'closed' in repr(p)
        for use in (p.start, p.join, p.is_alive, p.terminate,
                    lambda: p.exitcode, lambda: p.pid,
                    lambda: p.sentinel):
            with pytest.raises(ValueError, match='process object is closed'):
                use()
        p.close()  # closing twice is fine
