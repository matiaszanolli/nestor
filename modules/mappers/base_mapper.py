import numpy as np


class BaseMapper(object):

    def __init__(self, cartridge):
        self._cartridge = cartridge

    @property
    def prg(self):
        return self._cartridge.prg

    @property
    def chr(self):
        return self._cartridge.chr

    @property
    def sram(self):
        return self._cartridge.sram

    @property
    def mirror(self):
        return self._cartridge.mirror

    @mirror.setter
    def mirror(self, value):
        self._cartridge.mirror = value

    def read(self, address: np.uint16) -> np.uint8:
        raise NotImplementedError

    def write(self, address: np.uint16, value: np.uint8):
        raise NotImplementedError

    def step(self):
        raise NotImplementedError
