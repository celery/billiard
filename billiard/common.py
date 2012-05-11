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
        if self.T and now - self.T >= self.maxT:
            self.R = 0
        elif self.R >= self.maxR:
            raise self.RestartFreqExceeded("%r in %rs" % (self.R, self.maxT))
        self.R += 1
        self.T = now
