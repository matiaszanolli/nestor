import numpy as np

from .base_mapper import BaseMapper


class Mapper2(BaseMapper):
    """
    Mapper 0 games seem to be compatible with this one.
    """
    prg_banks = 0  # type: int
    prg_bank_1 = 0  # type: int

    def __init__(self, cartridge):
        self.prg_banks = len(cartridge.prg) / 0x4000
        prg_bank_2 = self.prg_banks - 1

    def step(self) -> None:
        pass

    def read(self, address: np.uint16) -> np.uint8:
        pass
        # TODO: finish

    def write(self, address: np.uint16, value: np.uint8):
        pass
        # TODO: finish
