import os
import signal
import time

import pytest

import billiard.pool
from billiard import get_context
from billiard.einfo import ExceptionWithTraceback
from billiard.exceptions import TimeLimitExceeded, WorkerLostError

from t import skip


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

def raise_base_exception():
    raise BaseException("base exception test")


def raise_system_exit():
    raise SystemExit(1)


def announce_pid_then_sleep(marker):
    """Publish the pid of the process actually running this job, then block.

    Written to a temporary name and renamed into place: os.replace is atomic,
    so the parent cannot observe the marker existing but still empty.

    The sleep must outlast the parent's result.get() timeout by a wide margin.
    If the two were comparable, a kill that was slow or ineffective would let
    the job finish at about the moment the get gave up, and the test would
    report whichever won rather than the behaviour it is checking.
    """
    with open(marker + '.tmp', 'w') as fh:
        fh.write(str(os.getpid()))
    os.replace(marker + '.tmp', marker)
    time.sleep(300)

def announce_pid_then_fail_in_cleanup(marker):
    """As above, but the job's own cleanup raises on the way out.

    A failing ``finally`` (or ``__exit__``) replaces the in-flight shutdown
    SystemExit with its own exception, so what arrives at the workloop is a
    RuntimeError. The job is no less unfinished for it.
    """
    try:
        with open(marker + '.tmp', 'w') as fh:
            fh.write(str(os.getpid()))
        os.replace(marker + '.tmp', marker)
        time.sleep(300)
    finally:
        raise RuntimeError('cleanup failed while shutting down')


class test_pool:
    def test_memory_error_from_callback_propagates(self):
        def callback(value):
            raise MemoryError(value)

        result = billiard.pool.ApplyResult({}, callback)

        with pytest.raises(MemoryError, match='out of memory'):
            result._set(None, (True, 'out of memory'))

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

    def test_timeout_handler_trywaitkill_without_getpgid(self, monkeypatch):
        monkeypatch.delattr(os, "getpgid", raising=False)
        monkeypatch.delattr(os, "killpg", raising=False)
        from unittest.mock import MagicMock
        worker = MagicMock()
        worker._name = "MockWorker-1"
        worker.pid = 12345
        worker._popen.wait.return_value = True

        handler = billiard.pool.TimeoutHandler([], {}, 0, 0)
        handler._trywaitkill(worker)
        worker.terminate.assert_called_once()

    def test_timeout_handler_trywaitkill_timeout_without_getpgid(self, monkeypatch):
        monkeypatch.delattr(os, "getpgid", raising=False)
        monkeypatch.delattr(os, "killpg", raising=False)
        from unittest.mock import MagicMock, patch
        worker = MagicMock()
        worker._name = "MockWorker-1"
        worker.pid = 12345
        worker._popen.wait.return_value = False

        handler = billiard.pool.TimeoutHandler([], {}, 0, 0)
        with patch("billiard.pool._kill") as mock_kill:
            handler._trywaitkill(worker)
            worker.terminate.assert_called_once()
            mock_kill.assert_called_once_with(worker.pid, billiard.pool.SIGKILL)

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

    def test_base_exception_propagates(self):
        pool = billiard.pool.Pool(1)
        result = pool.apply_async(raise_base_exception)

        with pytest.raises(BaseException, match="base exception test"):
            result.get(timeout=10)

        pool.close()
        pool.join()
        pool.terminate()

    def test_system_exit_from_task_replaces_worker(self):
        pool = billiard.pool.Pool(1)
        try:
            pid_before = pool.apply_async(os.getpid).get(timeout=10)
            result = pool.apply_async(raise_system_exit)
            with pytest.raises(SystemExit):
                result.get(timeout=10)
            pid_after = pool.apply_async(os.getpid).get(timeout=10)
            assert pid_after != pid_before
        finally:
            pool.terminate()
            pool.join()

    @skip.if_win32()
    @pytest.mark.parametrize('job', [
        announce_pid_then_sleep,
        announce_pid_then_fail_in_cleanup,
    ], ids=['plain', 'cleanup_raises'])
    def test_worker_terminated_mid_job_is_lost_not_completed(self, tmp_path,
                                                             job):
        """A worker told to exit did not finish its job.

        The SystemExit that terminates a worker is raised by billiard's own
        signal handler, inside whatever the worker happened to be running. If
        the worker reports that as the job's result, the job looks completed
        (with a failure) rather than interrupted -- and a caller that
        acknowledges work only once it is done, such as Celery with
        task_acks_late, then acknowledges a job nothing ever ran to the end.

        Run for two shapes of job. In the 'cleanup_raises' case the job's own
        finally raises while that SystemExit unwinds, so the exception
        reaching the workloop is a RuntimeError rather than the SystemExit --
        which is why the guard cannot be narrowed to SystemExit.

        Unix only, and deliberately so: on Windows os.kill maps to
        TerminateProcess, which never runs the Python-level handler. The
        worker would still die and the parent would still report the job
        lost, so this test would pass there without terminate_handler_fired()
        ever being consulted -- green, but not coverage.
        """
        pool = billiard.pool.Pool(1)
        try:
            marker = str(tmp_path / 'started')
            result = pool.apply_async(job, (marker,))

            # Take the pid from the child itself rather than from
            # pool._pool[0]: that indexes the pool's current roster, which is
            # only the process running this job as long as the pool has one
            # worker and the Supervisor has had no cause to replace it.
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline and not os.path.exists(marker):
                time.sleep(0.1)
            assert os.path.exists(marker), 'worker never started the job'
            with open(marker) as fh:
                worker_pid = int(fh.read())

            os.kill(worker_pid, billiard.pool.TERM_SIGNAL)

            # ApplyResult.get() re-raises ExceptionInfo.exception. The parent
            # synthesises this failure locally in Pool.mark_as_worker_lost, so
            # nothing is pickled and what surfaces is the
            # ExceptionWithTraceback wrapper, whose .exc holds the real
            # WorkerLostError -- `pytest.raises(WorkerLostError)` would NOT
            # match here. A result that had travelled back through the queue
            # would have been rebuilt by einfo.rebuild_exc into the bare
            # exception, hence the tolerant unwrap below.
            #
            # Naming both types keeps a TimeoutError -- the parent never
            # noticing the dead worker at all -- failing at the raises clause
            # with an accurate message, instead of reaching the assert.
            #
            # Generous timeout: the parent notices the dead worker from its
            # supervisor loop, so this bounds a failure rather than a wait.
            with pytest.raises(
                    (WorkerLostError, ExceptionWithTraceback)) as excinfo:
                result.get(timeout=30)
            exc = getattr(excinfo.value, 'exc', excinfo.value)
            assert isinstance(exc, WorkerLostError)
        finally:
            pool.terminate()
            pool.join()

    def test_hard_timeout_does_not_stall_pool(self):
        pool = billiard.pool.Pool(1, timeout=1)
        try:
            pid_before = pool.apply_async(os.getpid).get(timeout=10)
            result = pool.apply_async(time.sleep, (30,))
            with pytest.raises(Exception) as excinfo:
                result.get(timeout=10)
            exc = getattr(excinfo.value, 'exc', excinfo.value)
            assert isinstance(exc, TimeLimitExceeded)
            # Only submit again once the killed worker has been replaced;
            # otherwise the job may still be picked up by the dying worker.
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if pid_before not in [w.pid for w in pool._pool]:
                    break
                time.sleep(0.1)
            assert pool.apply_async(simple_task, (21,)).get(timeout=10) == 42
        except BaseException:
            # A stalled pool cannot be terminated either (terminate() blocks
            # on the same inqueue lock), so kill the workers outright and
            # skip the terminate-at-exit finalizer.
            for worker in pool._pool:
                try:
                    os.kill(worker.pid, signal.SIGKILL)
                except OSError:
                    pass
            pool._terminate.cancel()
            raise
        pool.terminate()
        pool.join()

    def test_on_ready_counter_is_synchronized(self):
        for ctx in ('spawn', 'fork', 'forkserver'):
            if ctx not in billiard.get_all_start_methods():
                continue
            pool = billiard.pool.Pool(processes=1, context=get_context(ctx))
            try:
                pool.apply_async(func, (1,)).get(timeout=10)
                on_ready_counter = pool.apply_async(get_on_ready_count, ).get(timeout=10)
                assert on_ready_counter == 1
            finally:
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


    def test_rejects_fewer_than_one_process(self):
        for processes in (0, -1):
            with pytest.raises(ValueError, match="at least 1"):
                billiard.pool.Pool(processes=processes)

    def test_rejects_non_positive_maxtasksperchild(self):
        # Worker only asserted this, so it failed with a bare AssertionError,
        # and under python -O the pool kept replacing workers that exited
        # before running a task.
        for maxtasksperchild in (0, -1, 1.5):
            with pytest.raises(ValueError, match="maxtasksperchild"):
                billiard.pool.Pool(processes=1,
                                   maxtasksperchild=maxtasksperchild)

    def test_rejects_bool_for_numeric_pool_args(self):
        """bool subclasses int; processes=True must not silently spawn 1 worker."""
        for kwargs in (
            {"processes": True},
            {"processes": False},
            {"maxtasksperchild": True},
            {"timeout": True},
            {"soft_timeout": True},
            {"lost_worker_timeout": True},
            {"max_memory_per_child": True},
            {"max_restarts": True},
            {"max_restart_freq": True},
        ):
            with pytest.raises(TypeError, match="bool"):
                billiard.pool.Pool(**kwargs)
