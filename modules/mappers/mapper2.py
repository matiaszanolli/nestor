import numpy as np

from .base_mapper import BaseMapper


class Mapper2(BaseMapper):
    """
    Mapper 0 games seem to be compatible with this one.
    """
    prg_banks = 0  # type: int
    prg_bank_1 = 0  # type: int

    def __init__(self, cartridge):
        super().__init__(cartridge)
        self.prg_banks = len(self.prg) // 0x4000
        self.prg_bank_1 = 0
        self.prg_bank_2 = self.prg_banks - 1

    def step(self) -> None:
        pass

    def read(self, address: np.uint16) -> np.uint8:
        if address < 0x2000:
            return self.chr[address]
        elif address >= 0xC000:
            index = self.prg_bank_2 * 0x4000 + int(address - 0xC000)
            return self.prg[index]
        elif address >= 0x8000:
            index = self.prg_bank_1 * 0x4000 + int(address - 0x8000)
            return self.prg[index]
        elif address >= 0x6000:
            index = int(address) - 0x6000
            return self.sram[index]
        else:
            raise Exception(f'unhandled mapper2 read at address: 0x{address}')

    def write(self, address: np.uint16, value: np.uint8):
        if address < 0x2000:
            self.chr[address] = value
        elif address >= 0x8000:
            self.prg_bank_1 = int(value) % self.prg_banks
        elif address >= 0x6000:
            index = int(address) - 0x6000
            self.sram[index] = value
        else:
            raise Exception(f'unhandled mapper2 write at address: 0x{address}')
