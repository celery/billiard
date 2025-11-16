import billiard.pool
from billiard import get_context
import time
import pytest


def func(x):
    if x == 2:
        raise ValueError
    return x


def get_on_ready_count():
    import inspect
    worker = inspect.stack()[1].frame.f_locals['self']
    return worker.on_ready_counter.value

def simple_task(x):
    return x * 2

class test_pool:
    def test_raises(self):
        pool = billiard.pool.Pool()
        assert pool.did_start_ok() is True
        pool.close()
        pool.terminate()

    def test_timeout_handler_iterates_with_cache(self):
        # Given a pool
        pool = billiard.pool.Pool()
        # If I have a cache containing async results
        cache = {n: pool.apply_async(n) for n in range(4)}
        # And a TimeoutHandler with that cache
        timeout_handler = pool.TimeoutHandler(pool._pool, cache, 0, 0)
        # If I call to handle the timeouts I expect no exception
        next(timeout_handler.handle_timeouts())

    def test_exception_traceback_present(self):
        pool = billiard.pool.Pool(1)
        results = [pool.apply_async(func, (i,)) for i in range(3)]

        time.sleep(1)
        pool.close()
        pool.join()
        pool.terminate()

        for i, res in enumerate(results):
            if i == 2:
                with pytest.raises(ValueError):
                    res.get()

    def test_on_ready_counter_is_synchronized(self):
        for ctx in ('spawn', 'fork', 'forkserver'):
            pool = billiard.pool.Pool(processes=1, context=get_context(ctx))
            pool.apply_async(func, (1,)).get(1)
            on_ready_counter = pool.apply_async(get_on_ready_count, ).get(1)
            assert on_ready_counter == 1
            pool.close()
            pool.join()
            pool.terminate()

    def test_graceful_shutdown_delivers_results(self):
        """Test that queued results are delivered during pool shutdown.
        
        Specifically, this test verifies that when _terminate_pool() is called,
        the ResultHandler.finish_at_shutdown() continues processing results
        that workers have placed in the outqueue.
        """

        # Create pool with threads=False so that the result handler thread does
        # not start and the task results are allowed to build up in the queue.
        pool = billiard.pool.Pool(processes=2, threads=False)

        # Submit tasks so that results are queued but not processed.
        results = [pool.apply_async(simple_task, (i,)) for i in range(8)]

        # Allow a small amount of time for tasks to complete.
        time.sleep(0.5)

        # Close and join the pool to ensure workers stop.
        pool.close()
        pool.join()

        # Call the _terminate_pool() class method to trigger the finish_at_shutdown()
        # function that will process results in the queue. Normally _terminate_pool()
        # is called by a Finalize object when the Pool object is destroyed. We cannot
        # call pool.terminate() here because it will call the Finalize object, which
        # won't do anything until the Pool object is destroyed at the end of this test.
        # We can simulate the shutdown behaviour by calling _terminate_pool() directly.
        billiard.pool.Pool._terminate_pool(
            pool._taskqueue,
            pool._inqueue,
            pool._outqueue,
            pool._pool,
            pool._worker_handler,
            pool._task_handler,
            pool._result_handler,
            pool._cache,
            pool._timeout_handler,
            pool._help_stuff_finish_args()
        )

        # Cancel the Finalize object to prevent _terminate_pool() from being called
        # a second time when the Pool object is destroyed.
        pool._terminate.cancel()

        # Verify that all results were delivered by finish_at_shutdown() and can be
        # retrieved.
        for i, result in enumerate(results):
            assert result.get() == i * 2
