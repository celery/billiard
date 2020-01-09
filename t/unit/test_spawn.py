from __future__ import absolute_import

import os
import sys
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
        return p.exitcode

    @pytest.mark.skipif(not sys.platform.startswith('linux'),
                        reason='set_pdeathsig() is supported only in Linux')
    def test_set_pdeathsig(self):
        q = Queue()
        p = Process(target=parent_task, args=(q,))
        p.start()
        child_proc = psutil.Process(q.get(timeout=3))
        p.terminate()
        assert child_proc.wait(3) is None

    @pytest.mark.skipif(not sys.platform.startswith('linux'),
                        reason='get_pdeathsig() is supported only in Linux')
    def test_set_get_pdeathsig(self):
        sig = get_pdeathsig()
        assert sig == 0
        set_pdeathsig(signal.SIGTERM)
        sig = get_pdeathsig()
        assert sig == signal.SIGTERM

def child_process(q):
    set_pdeathsig(signal.SIGTERM)
    q.put(os.getpid())
    while True:
        sleep(1)

def parent_task(q):
    p = Process(target=child_process, args=(q, ))
    p.start()
    p.join()

def task_from_process(name):
    print('proc:', name)

