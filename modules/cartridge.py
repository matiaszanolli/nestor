import logging
import numpy as np

from .mappers import get_mapper, BaseMapper

log = logging.getLogger("logging")


class Cartridge:

    prg: np.ndarray = None  # PRG cartridge ROM (program logic)
    chr: np.ndarray = None  # CHR cartridge ROM (graphics and sound data)
    mapper: BaseMapper = None
    mirror: np.uint8 = None
    sram: np.ndarray = np.ndarray((0x2000,), dtype=np.uint8)  # Save RAM (if any)

    def __init__(self, filename: str = None) -> None:
        self.prg = np.zeros((0x2000, ))
        self.mirror = np.uint8(0)
        if filename is not None:
            self.load(filename)

    def load(self, file: str):
        log.debug(f'Reading cartridge {file}...')
        with open(file, 'rb') as f:
            header = f.read(16)
            self._parse_header(header)

            # Read PRG ROM
            self.prg = np.frombuffer(f.read(self._prg_rom_pages * 0x4000), dtype=np.uint8)

            # Read CHR ROM
            self.chr = np.frombuffer(f.read(self._chr_rom_pages * 0x2000), dtype=np.uint8)

            self.mapper = self.load_mapper(self._mapper_id)
            log.debug(f'Uses mapper: {self.mapper.__class__}')

    def _parse_header(self, header: bytes) -> None:
        # Verify legal header.
        if header[0:4] != b'NES\x1a':
            raise Exception('Invalid file header.')

        self._header = header
        self._prg_rom_pages = header[4]
        log.debug(f'Program ROM pages: {self._prg_rom_pages}')
        self._chr_rom_pages = header[5]
        log.debug(f'Character ROM pages: {self._chr_rom_pages}')
        self._flags6 = header[6]
        self._flags7 = header[7]

        if self._flags7 & 0b100:
            # NES 2.0 format
            raise Exception('NES 2.0 format not yet implemented.')

        # iNES format
        self._prg_ram_size = header[8]
        self._flags9 = header[9]
        self._flags10 = header[10]

        # Determine mapper ID
        self._mapper_id = self._flags6 >> 4
        if header[11:15] is b'\x00\x00\x00\x00':
            self._mapper_id += (self._flags7 >> 4) << 4

    def load_mapper(self, mapper_id: int) -> BaseMapper:
        return get_mapper(self, mapper_id)
