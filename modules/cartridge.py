import logging
import numpy as np

from .mappers import get_mapper, BaseMapper

log = logging.getLogger("logging")


class Cartridge(object):

    prg = None  # type: np.ndarray
    chr = None  # type: np.ndarray
    mapper = None  # type: BaseMapper
    mirror = None  # type: np.uint8
    sram = np.ndarray((0x2000,), dtype=np.uint8)

    def __init__(self, filename=None):
        self.prg = np.zeros((0x2000, ))
        self.mirror = np.uint8(0)
        if filename is not None:
            self.load(filename)

    def load(self, file):
        log.debug("Reading cartridge '{0}'...".format(file))
        with open(file, "rb") as f:
            header = f.read(16)
            self._parse_header(header)

            # Read PRG ROM
            self.prg = f.read(self._prg_rom_pages * 0x4000)

            # Read CHR ROM
            self.chr = f.read(self._chr_rom_pages * 0x2000)

            self.mapper = self.load_mapper(self._mapper_id)
            log.debug("Uses mapper: {0}".format(self.mapper.__class__))

    def _parse_header(self, header: bytes) -> None:
        # Verify legal header.
        if header[0:4] != b"NES\x1a":
            raise Exception("Invalid file header.")

        self._header = header
        self._prg_rom_pages = header[4]
        log.debug("Program ROM pages: {0}".format(self._prg_rom_pages))
        self._chr_rom_pages = header[5]
        log.debug("Character ROM pages: {0}".format(self._chr_rom_pages))
        self._flags6 = header[6]
        self._flags7 = header[7]

        if self._flags7 & 0b100:
            # NES 2.0 format
            raise Exception("NES 2.0 format not yet implemented.")

        # iNES format
        self._prg_ram_size = header[8]
        self._flags9 = header[9]
        self._flags10 = header[10]

        # Determine mapper ID
        self._mapper_id = self._flags6 >> 4
        if header[11:15] is b"\x00\x00\x00\x00":
            self._mapper_id += (self._flags7 >> 4) << 4

    def load_mapper(self, mapper_id: int):
        return get_mapper(self, mapper_id)  # TODO: Implement mappers
