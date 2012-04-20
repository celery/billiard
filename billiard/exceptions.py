from __future__ import absolute_import

from multiprocessing import (
    ProcessError,
    BufferTooShort,
    TimeoutError,
    AuthenticationError,
)

class TimeLimitExceeded(Exception):
    """The time limit has been exceeded and the job has been terminated."""


class SoftTimeLimitExceeded(Exception):
    """The soft time limit has been exceeded. This exception is raised
    to give the task a chance to clean up."""


class WorkerLostError(Exception):
    """The worker processing a job has exited prematurely."""


