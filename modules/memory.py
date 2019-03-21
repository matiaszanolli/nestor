import numpy as np
from typing import List


class Memory(object):
    def __init__(self):
        self._memory = [0] * 0xffff  # type: List[np.uint16]

    def read(self, address: np.uint16, length=0x0800) -> np.uint8:
        """
        Returns an 8-bit chunk of memory from a given address.
        :param address: a location between 0x0000 and 0xFFFF
        :param length: a custom read length (8 or 16 bits)
        :return: byte
        """
        from main import Manager

        manager = Manager.get()

        if address < 0x2000:
            # The lower 2KB are the system main RAM, so can be assigned directly
            return self._memory[int(address % 0x0800)]
        elif address < 0x4000:
            # PPU registers
            return manager.ppu.read_register(0x2000 + address % 8)
        elif address < 0x4014:
            # APU registers
            raise NotImplementedError()  # TODO: Implement APU operations
        elif address == 0x4014:
            # PPU register
            return manager.ppu.read_register(address)
        elif address in (0x4015, 0x4017):
            # More APU registers
            raise NotImplementedError()  # TODO: Implement APU operations
        elif address == 0x4016 or address < 0x6000:
            # I/O registers
            raise NotImplementedError()  # TODO: Implement I/O operations
        else:
            # Cartridge mapper registers
            return manager.mapper.read(address)

    def write(self, address: np.uint16, value: np.uint8, length=0x0800):
        """
        Writes an 8-bit chunk of memory in a specified address.
        :param address: a location between 0x0000 and 0xFFFF
        :param length: a custom write length (8 or 16 bits)
        :param value: the byte to be written
        """

        if address < 0x2000:
            # The lower 2KB are the system main RAM, so can be assigned directly
            self._memory[address % 0x0800] = value
        elif address < 0x4000:
            # PPU registers
            raise NotImplementedError()  # TODO: Implement PPU operations
        elif address < 0x4014:
            # APU registers
            raise NotImplementedError()  # TODO: Implement APU operations
        elif address == 0x4014:
            # PPU register
            raise NotImplementedError()  # TODO: Implement PPU operations
        elif address in (0x4015, 0x4017):
            # More APU registers
            raise NotImplementedError()  # TODO: Implement APU operations
        elif address == 0x4016 or address < 0x6000:
            # I/O registers
            raise NotImplementedError()  # TODO: Implement I/O operations
        else:
            raise ValueError('Unhandled memory write at {}'.format(address))

    def read16(self, address: np.uint16):
        """
        Reads a 16-bit chunk of memory in a specified address.
        :param address: uint16
        :return: int
        """
        return self.read(address, 0x1000)

    def read16bug(self, address: np.uint16):
        """
        Taken from fogleman's source, "emulates a 6502 bug that caused the low 
        byte to wrap without incrementing the high byte"
        :param address: 
        :return: word
        """
        a = address
        b = np.uint16(a & 0xFF00) | np.uint16(a + 1)
        lo = self.read(a)
        hi = self.read(b)
        return (hi << 8) | lo

    def write16(self, address, value):
        """
        Writes a 16-bit chunk of memory in a specified address.
        :param address: a location between 0x0000 and 0xFFFF
        :param value: the byte to be written
        """
        self.write(address, value, 0x1000)


class PPUMemory(object):

    MIRROR_HORIZONTAL = 0
    MIRROR_VERTICAL = 1
    MIRROR_SINGLE_0 = 2
    MIRROR_SINGLE_1 = 3
    MIRROR_FOUR = 4

    def __init__(self):
        from ..main import Manager
        self.console = Manager.get()

    def read(self, address: np.uint16) -> np.uint8:
        address = address % 0x4000
        if address < 0x2000:
            return self.console.mapper.read(address)
        elif address < 0x3F00:
            pass
        # TODO: finish