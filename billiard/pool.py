from billiard._pool import Pool, SoftTimeLimitExceeded


class DynamicPool(Pool):
    """Version of :class:`multiprocessing.Pool` that can dynamically grow
    in size."""
    SoftTimeLimitExceeded = SoftTimeLimitExceeded

