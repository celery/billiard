import os
import subprocess
import sys
import textwrap
from billiard import get_context, Process, Queue
from billiard.util import set_pdeathsig, get_pdeathsig
import pytest
import psutil
import signal
from time import sleep

class test_spawn:
    def test_start(self):
        ctx = get_context('spawn')

        p = ctx.Process(target=task_from_process, args=('opa',))
        p.start()
        p.join()
        assert p.exitcode == 0

    def test_start_with_target_in_main_script(self, tmp_path):
        """A target defined in a script run as __main__ can be unpickled.

        The script's __main__ has no __spec__, so the child has to re-run it
        by path to find the target.
        """
        result = run_script(tmp_path, '''
            import sys
            import billiard

            def target():
                print('hello from child')

            if __name__ == '__main__':
                p = billiard.get_context('spawn').Process(target=target)
                p.start()
                p.join()
                sys.exit(p.exitcode)
        ''')
        assert result.returncode == 0, result.stderr
        assert result.stdout == 'hello from child\n'

    def test_pool_in_process_spawned_by_multiprocessing(self, tmp_path):
        """A pool works in a process spawned by multiprocessing from a script.

        That process runs the script as __mp_main__, which can't be imported
        by name. Pool workers told to import it die and are replaced forever,
        so the result is waited for with a timeout.
        """
        result = run_script(tmp_path, '''
            import multiprocessing
            import sys
            import billiard

            def run_pool():
                with billiard.get_context('spawn').Pool(1) as pool:
                    res = pool.apply_async(str.upper, ('hello from pool',))
                    print(res.get(timeout=30))

            if __name__ == '__main__':
                ctx = multiprocessing.get_context('spawn')
                p = ctx.Process(target=run_pool)
                p.start()
                p.join()
                sys.exit(p.exitcode)
        ''')
        assert result.returncode == 0, result.stderr
        assert result.stdout == 'HELLO FROM POOL\n'

    @pytest.mark.skipif(not sys.platform.startswith('linux'),
                        reason='set_pdeathsig() is supported only in Linux')
    def test_set_pdeathsig(self):
        success = "done"
        q = Queue()
        p = Process(target=parent_task, args=(q, success))
        p.start()
        child_proc = psutil.Process(q.get(timeout=3))
        try:
            p.terminate()
            assert q.get(timeout=3) == success
        finally:
            child_proc.terminate()

    @pytest.mark.skipif(not sys.platform.startswith('linux'),
                        reason='get_pdeathsig() is supported only in Linux')
    def test_set_get_pdeathsig(self):
        sig = get_pdeathsig()
        assert sig == 0
        set_pdeathsig(signal.SIGTERM)
        sig = get_pdeathsig()
        assert sig == signal.SIGTERM

def child_process(q, success):
    sig = signal.SIGUSR1
    class ParentDeathError(Exception):
        pass

    def handler(*args):
        raise ParentDeathError()

    signal.signal(sig, handler)
    set_pdeathsig(sig)
    q.put(os.getpid())
    try:
        while True:
            sleep(1)
    except ParentDeathError:
        q.put(success)
    sys.exit(0)

def parent_task(q, success):
    p = Process(target=child_process, args=(q, success))
    p.start()
    p.join()

def task_from_process(name):
    print('proc:', name)

def run_script(tmp_path, source):
    """Run *source* as a script file, so that it is the parent's __main__."""
    script = tmp_path / 'script.py'
    script.write_text(textwrap.dedent(source))
    return subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, timeout=120,
    )

