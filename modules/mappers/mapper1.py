import numpy as np

from .base_mapper import BaseMapper


class Mapper1(BaseMapper):

    def __init__(self, cartridge):
        super().__init__(cartridge)
        self.shift_register = np.uint8(0x10)
        self.control = np.uint8(0)
        self.prg_mode = np.uint8(0)
        self.chr_mode = np.uint8(0)
        self.prg_bank = np.uint8(0)
        self.chr_bank0 = np.uint8(0)
        self.chr_bank1 = np.uint8(0)
        self.prg_offsets = np.zeros(shape=(2,), dtype=np.uint8)
        self.chr_offsets = np.zeros(shape=(2,), dtype=np.uint8)
        self.prg_offsets[1] = self.prg_bank_offset(-1)

    def step(self):
        pass

    def read(self, address: np.uint16) -> np.uint8:
        if address < 0x2000:  # CHR read
            bank = address // 0x1000
            offset = address % 0x1000
            return self.chr[self.chr_offsets[bank] + int(offset)]
        elif address >= 0x8000:  # PRG read
            address = address - 0x8000
            bank = address // 0x4000
            offset = address % 0x4000
            return self.prg[self.prg_offsets[bank] + int(offset)]
        elif address >= 0x6000:  # SRAM read
            return self.sram[int(address) - 0x6000]
        else:
            raise Exception(f'unhandled mapper1 read at address: {hex(address)}')

    def write(self, address: np.uint16, value: np.uint8):
        if address < 0x2000:  # CHR write
            bank = address // 0x1000
            offset = address % 0x1000
            self.chr[self.chr_offsets[bank] + int(offset)] = value
        elif address >= 0x8000:
            self.load_register(address, value)
        elif address >= 0x6000:
            self.sram[int(address) - 0x6000] = value
        else:
            raise Exception(f'unhandled mapper1 write at address: {hex(address)}')

    def load_register(self, address: np.uint16, value: np.uint8):
        if value & 0x80 == 0x80:
            self.shift_register = np.uint8(0x10)
            self.write_control(self.control | 0x0C)
        else:
            complete = self.shift_register & 1 == 1
            self.shift_register >>= 1
            self.shift_register |= (value & 1) << 4
            if complete:
                self.write_register(address, np.uint8(self.shift_register))
                self.shift_register = np.uint8(0x10)

    def write_register(self, address: np.uint16, value: np.uint8):
        if address <= 0x9FFF:
            self.write_control(value)
        elif address <= 0xBFFF:
            self.write_chr_bank_0(value)
        elif address <= 0xDFFF:
            self.write_chr_bank_1(value)
        elif address <= 0xFFFF:
            self.write_prg_bank(value)

    def write_chr_bank_0(self, value: np.uint8):
        # CHR bank 0 (internal, $A000-$BFFF)
        self.chr_bank0 = value
        self.update_offsets()

    def write_chr_bank_1(self, value: np.uint8):
        # CHR bank 1 (internal, $C000-$DFFF)
        self.chr_bank1 = value
        self.update_offsets()

    def write_prg_bank(self, value: np.uint8):
        # PRG bank (internal, $E000-$FFFF)
        self.prg_bank = value & 0x0F
        self.update_offsets()

    def write_control(self, value: np.uint8):
        self.control = value
        self.chr_mode = (value >> 4) & 1
        self.prg_mode = (value >> 2) & 3
        mirror = value & 3

        if mirror == 0:
            self.mirror = 2  # MirrorSingle0
        elif mirror == 1:
            self.mirror = 3  # MirrorSingle1
        elif mirror == 2:
            self.mirror = 1  # MirrorVertical
        elif mirror == 3:
            self.mirror = 0  # MirrorHorizontal

        self.update_offsets()

    def update_offsets(self):
        if self.prg_mode in (0, 1,):  # switch 32 KB at $8000, ignoring low bit of bank number
            self.prg_offsets[0] = self.prg_bank_offset(int(self.prg_bank & 0xFE))
            self.prg_offsets[1] = self.prg_bank_offset(int(self.prg_bank | 0x01))
        elif self.prg_mode == 2:  # fix first bank at $8000 and switch 16 KB bank at $C000
            self.prg_offsets[0] = 0
            self.prg_offsets[1] = self.prg_bank_offset(int(self.prg_bank))
        elif self.prg_mode == 3:  # fix last bank at $C000 and switch 16 KB bank at $8000
            self.prg_offsets[0] = self.prg_bank_offset(int(self.prg_bank))
            self.prg_offsets[1] = self.prg_bank_offset(-1)

        if self.chr_mode == 0:  # switch 8 KB at a time
            self.chr_offsets[0] = self.chr_bank_offset(int(self.chr_bank0 & 0xFE))
            self.chr_offsets[1] = self.chr_bank_offset(int(self.chr_bank0 | 0x01))
        elif self.chr_mode == 1:  # switch two separate 4 KB banks
            self.chr_offsets[0] = self.chr_bank_offset(int(self.chr_bank0))
            self.chr_offsets[1] = self.chr_bank_offset(int(self.chr_bank1))

    def prg_bank_offset(self, index: int) -> int:
        if index >= 0x80:
            index -= 0x100
        index %= len(self.prg) // 0x4000
        offset = index * 0x4000
        if offset < 0:
            offset += len(self.prg)
        return offset

    def chr_bank_offset(self, index: int) -> int:
        if index >= 0x80:
            index -= 0x100
        index %= len(self.chr) // 0x1000
        offset = index * 0x1000
        if offset < 0:
            offset += len(self.chr)
        return offset
