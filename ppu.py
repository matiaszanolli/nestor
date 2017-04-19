import numpy as np
from .memory import Memory
from typing import List


class PPU(object):

    memory = None
    cycle = 0  # type: int
    scanline = 0  # type: int
    frame = 0  # type: np.uint64
    palette = []  # type: List[tuple]

    # Registers
    v = None  # type: np.uint16
    t = None  # type: np.uint16
    x = None  # type: np.uint8
    w = None  # type: np.uint8
    f = None  # type: np.uint8

    # Flags
    nmi_occurred = None  # type: bool
    nmi_output = None  # type: bool
    nmi_previous = None  # type: bool
    nmi_delay = None  # type: np.uint8

    oam_address = None  # type: np.uint8

    def __init__(self, memory: Memory):
        self._palette = [(0x75, 0x75, 0x75),
                         (0x27, 0x1b, 0x8f),
                         (0x00, 0x00, 0xab),
                         (0x47, 0x00, 0x9f),
                         (0x8f, 0x00, 0x77),
                         (0xab, 0x00, 0x13),
                         (0xa7, 0x00, 0x00),
                         (0x7f, 0x0b, 0x00),
                         (0x43, 0x2f, 0x00),
                         (0x00, 0x47, 0x00),
                         (0x00, 0x51, 0x00),
                         (0x00, 0x3f, 0x17),
                         (0x1b, 0x3f, 0x5f),
                         (0x00, 0x00, 0x00),
                         (0x00, 0x00, 0x00),
                         (0x00, 0x00, 0x00),
                         (0xbc, 0xbc, 0xbc),
                         (0x00, 0x73, 0xef),
                         (0x23, 0x3b, 0xef),
                         (0x83, 0x00, 0xf3),
                         (0xbf, 0x00, 0xbf),
                         (0xe7, 0x00, 0x5b),
                         (0xdb, 0x2b, 0x00),
                         (0xcb, 0x4f, 0x0f),
                         (0x8b, 0x73, 0x00),
                         (0x00, 0x97, 0x00),
                         (0x00, 0xab, 0x00),
                         (0x00, 0x93, 0x3b),
                         (0x00, 0x83, 0x8b),
                         (0x00, 0x00, 0x00),
                         (0x00, 0x00, 0x00),
                         (0x00, 0x00, 0x00),
                         (0xff, 0xff, 0xff),
                         (0x3f, 0xbf, 0xff),
                         (0x5f, 0x97, 0xff),
                         (0xa7, 0x8b, 0xfd),
                         (0xf7, 0x7b, 0xff),
                         (0xff, 0x77, 0xb7),
                         (0xff, 0x77, 0x63),
                         (0xff, 0x9b, 0x3b),
                         (0xf3, 0xbf, 0x3f),
                         (0x83, 0xd3, 0x13),
                         (0x4f, 0xdf, 0x4b),
                         (0x58, 0xf8, 0x98),
                         (0x00, 0xeb, 0xdb),
                         (0x00, 0x00, 0x00),
                         (0x00, 0x00, 0x00),
                         (0x00, 0x00, 0x00),
                         (0xff, 0xff, 0xff),
                         (0xab, 0xe7, 0xff),
                         (0xc7, 0xd7, 0xff),
                         (0xd7, 0xcb, 0xff),
                         (0xff, 0xc7, 0xff),
                         (0xff, 0xc7, 0xdb),
                         (0xff, 0xbf, 0xb3),
                         (0xff, 0xdb, 0xab),
                         (0xff, 0xe7, 0xa3),
                         (0xe3, 0xff, 0xa3),
                         (0xab, 0xf3, 0xbf),
                         (0xb3, 0xff, 0xcf),
                         (0x9f, 0xff, 0xf3),
                         (0x00, 0x00, 0x00),
                         (0x00, 0x00, 0x00),
                         (0x00, 0x00, 0x00)]

        self.memory = memory
        self.palette_data = np.ndarray((32, ), dtype=np.uint8)
        self.nametable_data = np.ndarray((2048, ), dtype=np.uint8)
        self.oam_data = np.ndarray((2048, ), dtype=np.uint8)

        self.reset()

    def reset(self) -> None:
        self.cycle = 340
        self.scanline = 240
        self.frame = 0
        self.write_control(0)
        self.write_mask(0)
        self.write_oam_address(0)

    def write_oam_address(self, value: np.uint8) -> None:
        self.oam_address = value




