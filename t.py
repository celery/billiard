import billiard as mp
from setproctitle import setproctitle
import time

def initfun():
    setproctitle("Pool: %s" % mp.current_process()._name)

def f(x):
    print("TASK")
    return True


def cb(res):
    print("GOT: %r" % (res, ))



def main():
    mp.forking_enable(False)
    initfun()
    x = mp.Pool(1, initializer=initfun)
    time.sleep(10)
    x.apply_async(f, ("x" * 1024**2, ), callback=cb)
    time.sleep(3)
    x.apply_async(f, ("x" * (1024**2), ), callback=cb)
    time.sleep(3)
    x.apply_async(f, ("x" * (1024**2), ), callback=cb)

    time.sleep(30)

    x.close()
    x.join()


if __name__ == "__main__":
    main()
