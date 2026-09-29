import pytest

from billiard import JoinableQueue, Queue


class test_closed_queue:

    @pytest.mark.parametrize('queue_type', [Queue, JoinableQueue])
    def test_put_raises_value_error(self, queue_type):
        # put() only asserted this, so under python -O the item was
        # accepted and then lost by the feeder thread.
        q = queue_type()
        q.close()
        with pytest.raises(ValueError, match='is closed'):
            q.put(1)
        with pytest.raises(ValueError, match='is closed'):
            q.put_nowait(1)

    @pytest.mark.parametrize('queue_type', [Queue, JoinableQueue])
    def test_get_raises_value_error(self, queue_type):
        q = queue_type()
        q.close()
        with pytest.raises(ValueError, match='is closed'):
            q.get()
        with pytest.raises(ValueError, match='is closed'):
            q.get(timeout=0.1)
        with pytest.raises(ValueError, match='is closed'):
            q.get_nowait()
