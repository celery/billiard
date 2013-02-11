from __future__ import absolute_import

from time import time

from .exceptions import RestartFreqExceeded


class restart_state(object):
    RestartFreqExceeded = RestartFreqExceeded

    def __init__(self, maxR, maxT):
        self.maxR, self.maxT = maxR, maxT
        self.R, self.T = 0, None

    def step(self):
        now = time()
        R = self.R
        if self.T and now - self.T >= self.maxT:
            self.R = 0
        elif self.maxR and R >= self.maxR:
            # verify that R has a value as it may have been reset
            # by another thread, and we want to avoid locking.
            if self.R:
                raise self.RestartFreqExceeded(
                    "%r in %rs" % (self.R, self.maxT),
                )
        self.R += 1
        self.T = now
