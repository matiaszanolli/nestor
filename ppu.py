import numpy as np
from .memory import Memory
from typing import List
from pyglet.graphics import Batch


class PPU(object):

    # Memory interface
    memory = None
    cycle = 0  # type: int
    scanline = 0  # type: int
    frame = None  # type: Batch
    frame_number = 0  # type: int
    palette = []  # type: List[tuple]

    '''
    Registers:
    v = current vram address (15 bit)
    t = temporary vram address (15 bit)
    x = fine x scroll (3 bit)
    w = write toggle (1 bit)
    f = even/odd frame flag (1 bit)
    '''
    v = None  # type: np.uint16
    t = None  # type: np.uint16
    x = None  # type: np.uint8
    w = None  # type: np.uint8
    f = None  # type: np.uint8

    register = None

    # Flags
    nmi_occurred = None  # type: bool
    nmi_output = None  # type: bool
    nmi_previous = None  # type: bool
    nmi_delay = None  # type: np.uint8
    flag_name_table = None
    flag_increment = None
    flag_sprite_table = None
    flag_background_table = None
    flag_sprite_size = None
    flag_master_slave = None
    flag_grayscale = None
    flag_show_left_background = None
    flag_show_left_sprites = None
    flag_show_background = None
    flag_show_sprites = None
    flag_red_tint = None
    flag_green_tint = None
    flag_blue_tint = None
    flag_sprite_overflow = None
    flag_sprite_zero_hit = None

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
        self.frame = Batch()

        self.reset()

    def reset(self) -> None:
        self.cycle = 340
        self.scanline = 240
        self.frame_number = 0
        self.write_control(np.uint8(0))
        self.write_mask(0)
        self.write_oam_address(0)

    """
    OAM HANDLING METHODS
    The OAM (Object Attribute Memory) is internal memory inside the PPU that 
    contains a display list of up to 64 sprites, where each sprite's 
    information occupies 4 bytes.
    """
    def write_control(self, value: np.uint8) -> None:
        """
        Controller ($2000) > write
        Common name: PPUCTRL
        Description: PPU control register
        Access: write
        :param value: byte
        """
        self.flag_name_table = (value >> 0) & 3
        self.flag_increment = (value >> 2) & 1
        self.flag_sprite_table = (value >> 3) & 1
        self.flag_background_table = (value >> 4) & 1
        self.flag_sprite_size = (value >> 5) & 1
        self.flag_master_slave = (value >> 6) & 1
        self.nmi_output = (value >> 7) & 1 == 1
        self.nmi_change()
        self.t = (self.t & 0xF3FF) | ((np.uint16(value) & 0x03) << 10)

    def write_mask(self, value: np.uint8) -> None:
        """
        Mask ($2001) > write
        Common name: PPUMASK
        Description: PPU mask register
        Access: write
        This register controls the rendering of sprites and backgrounds, as 
        well as colour effects.
        :param value: byte
        """
        self.flag_grayscale = (value >> 0) & 1
        self.flag_show_left_background = (value >> 1) & 1
        self.flag_show_left_sprites = (value >> 2) & 1
        self.flag_show_background = (value >> 3) & 1
        self.flag_show_sprites = (value >> 4) & 1
        self.flag_red_tint = (value >> 5) & 1
        self.flag_green_tint = (value >> 6) & 1
        self.flag_blue_tint = (value >> 7) & 1

    def read_status(self) -> np.uint8:
        """
        ($2002) > Read only: The PPU Status Register is used by the PPU to 
        report its status to the CPU.
        :return: byte
        """
        result = self.register & 0x1F
        result |= self.flag_sprite_overflow << 5
        result |= self.flag_sprite_zero_hit << 6
        if self.nmi_occurred:
            result |= 1 << 7
        self.nmi_occurred = False
        self.nmi_change()
        self.w = 0
        return np.uint8(result)

    def write_oam_address(self, value: np.uint8) -> None:
        """
        $2003 (OAMADDR): Write the address of OAM you want to access here. 
        Most games just write $00 here and then use OAMDMA.
        :param value: byte
        """
        self.oam_address = value

    def read_oam_data(self) -> np.uint8:
        """
        $2004 (OAMDATA - read): Same as before, most games use OAMDMA instead.
        :return: byte
        """
        return self.oam_data[self.oam_address]

    def write_oam_data(self, value: np.uint8) -> None:
        """
        $2004 (OAMDATA - write): Same as before, most games use OAMDMA instead.
        On the real NES, there are far fewer random sprite glitches when you 
        use sprite DMA transfer than when you just poke sprite values to
        SPR-RAM.
        :param value: byte
        """
        self.oam_data[self.oam_address] = value
        self.oam_address += 1

    def write_scroll(self, value: np.uint8) -> None:
        """
        $2005 (Scroll): This register is used to change the scroll position, 
        that is, to tell the PPU which pixel of the nametable selected through 
        PPUCTRL should be at the top left corner of the rendered screen.
        :param value: byte
        """
        if self.w == 0:
            self.t = (self.t & 0xFFE0) | (np.uint16(value) >> 3)
            self.x = value & 0x07
            self.w = 1
        else:
            self.t = (self.t & 0x8FFF) | ((np.uint16(value) & 0x07) << 12)
            self.t = (self.t & 0xFC1F) | ((np.uint16(value) & 0xF8) << 2)
            self.w = 0



