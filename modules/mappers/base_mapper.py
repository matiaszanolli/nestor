import numpy as np


class BaseMapper(object):

    def __init__(self, cartridge) -> None:
        self._cartridge = cartridge

    @property
    def prg(self) -> np.ndarray:
        return self._cartridge.prg

    @property
    def chr(self) -> np.ndarray:
        return self._cartridge.chr

    @property
    def sram(self) -> np.ndarray:
        return self._cartridge.sram

    @property
    def mirror(self) -> np.uint8:
        return self._cartridge.mirror

    @mirror.setter
    def mirror(self, value: np.uint8) -> None:
        self._cartridge.mirror = value

    def read(self, address: np.uint16) -> np.uint8:
        raise NotImplementedError

    def write(self, address: np.uint16, value: np.uint8) -> None:
        raise NotImplementedError

    def step(self) -> None:
        raise NotImplementedError
