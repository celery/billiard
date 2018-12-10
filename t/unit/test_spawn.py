from __future__ import absolute_import

import sys
from billiard import get_context, Value, Process, Event
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
        return_pid = Value('i')
        p = Process(target=parent_task, args=(return_pid,))
        p.start()
        sleep(3) # wait for setting pdeathsig
        p.terminate()
        sleep(3) # wait for process termination
        with pytest.raises(psutil.NoSuchProcess):
            proc = psutil.Process(return_pid.value)

    @pytest.mark.skipif(not sys.platform.startswith('linux'),
                        reason='get_pdeathsig() is supported only in Linux')
    def test_set_get_pdeathsig(self):
        sig = get_pdeathsig()
        assert sig == 0
        set_pdeathsig(signal.SIGTERM)
        sig = get_pdeathsig()
        assert sig == signal.SIGTERM

def child_process():
    set_pdeathsig(signal.SIGTERM)
    while True:
        sleep(1)

def parent_task(return_pid):
    p = Process(target=child_process)
    p.start()
    sleep(1) # Wait for starting process
    return_pid.value = p.pid

def task_from_process(name):
    print('proc:', name)

