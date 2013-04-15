import atexit


def teardown():
    cancelled = set()
    import billiard.util
    cancelled.add(billiard.util._exit_function)

    try:
        import multiprocessing.util
        cancelled.add(multiprocessing.util._exit_function)
    except (AttributeError, ImportError):
        pass

    atexit._exithandlers[:] = [
        e for e in atexit._exithandlers if e[0] not in cancelled
    ]
