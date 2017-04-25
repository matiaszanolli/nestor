import numpy as np


class BaseMapper(object):

    def read(self, address: np.uint16) -> np.uint8:
        raise NotImplementedError

    def write(self, address: np.uint16, value: np.uint8):
        raise NotImplementedError

    def step(self):
        raise NotImplementedError
