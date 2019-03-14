import logging
import numpy as np
from typing import List
from pyglet.graphics import Batch
from .memory import Memory


class PPU(object):

    # Memory interface
    memory = None
    cycle = 0  # type: int
    scanline = 0  # type: int
    frame = 0  # type: int
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
    v = 0  # type: np.uint16
    t = 0  # type: np.uint16
    x = 0  # type: np.uint8
    w = 0  # type: np.uint8
    f = 0  # type: np.uint8

    register = None

    # Flags
    nmi_occurred = False  # type: bool
    nmi_output = False  # type: bool
    nmi_previous = False  # type: bool
    nmi_delay = 0  # type: np.uint8
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

    tile_data = 0
    sprite_count = 0
    front = None
    back = None
    attribute_table_byte = None

    oam_address = None  # type: np.uint8

    def __init__(self, memory: Memory):
        self.palette_data = [(0x75, 0x75, 0x75),
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
        # self.palette_data = np.ndarray((32, ), dtype=np.uint8)
        self.nametable_data = np.ndarray((2048, ), dtype=np.uint8)
        self.oam_data = np.ndarray((2048, ), dtype=np.uint8)
        self.frame = 0

        self.reset()

    def reset(self) -> None:
        logging.info('Resetting PPU...')
        self.cycle = 340
        self.scanline = 240
        self.frame_number = 0
        self.write_control(np.uint8(0))
        self.write_mask(np.uint8(0))
        self.write_oam_address(np.uint8(0))

    def read_register(self, address: np.uint16) -> np.uint8:
        """
        Makes a read operation based on the specified register address.
        :param address: uint16
        :return: byte
        """
        if address == 0x2002:
            return self.read_status()
        elif address == 0x2004:
            return self.read_oam_data()
        elif address == 0x2007:
            return self.read_data()
        return np.uint8(0)

    def write_register(self, address: np.uint16, value: np.uint8):
        """
        According to a given register address and 8-bit value, performs a
        write operation.
        :param address: uint16
        :param value: byte
        """
        self.register = value
        if address == 0x2000:
            self.write_control(value)
        elif address == 0x2001:
            self.write_mask(value)
        elif address == 0x2003:
            self.write_oam_address(value)
        elif address == 0x2004:
            self.write_oam_data(value)
        elif address == 0x2005:
            self.write_scroll(value)
        elif address == 0x2006:
            self.write_address(value)
        elif address == 0x2007:
            self.write_data(value)
        elif address == 0x4014:
            self.write_dma(value)

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
        $2005 (PPUSCROLL): This register is used to change the scroll position, 
        that is, to tell the PPU which pixel of the nametable selected through 
        PPUCTRL should be at the top left corner of the rendered screen.
        This function should always be called twice.
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

    def write_address(self, value: np.uint8) -> None:
        """
        $2006 (PPUADDR): Designed for the CPU to write on VRAM through a pair 
        of registers on the PPU. First it loads an address into PPUADDR, 
        and then it writes repeatedly to PPUDATA to fill VRAM.
        This function should always be called twice.
        :param value: byte
        """
        if self.w == 0:
            self.t = (self.t & 0x80FF) | ((np.uint16(value) & 0x3F) << 8)
            self.w = 1
        else:
            self.t = (self.t & 0xFF00) | np.uint16(value)
            self.v = self.t
            self.w = 1

    def read_data(self) -> np.uint8:
        """
        $2007 (PPUDATA - read): VRAM read/write data register. 
        After access, the video memory address will increment by an amount 
        determined by $2000:2.

        :return: byte
        """
        value = self.memory.read(self.v)
        if self.v % 0x4000 < 0x3F00:
            # emulate buffered reads
            buffered = self.buffered_data
            self.buffered_data = value
            value = buffered
        else:
            self.buffered_data = self.memory.read(self.v - 0x1000)
        if self.flag_increment == 0:
            self.v += 1
        else:
            self.v += 32
        return value

    def write_data(self, value: np.uint8) -> None:
        """
        $2007 (PPUDATA - write): VRAM read/write data register. 
        After access, the video memory address will increment by an amount 
        determined by $2000:2.
 
        :param value: byte
        """
        self.write(self.v, value)
        if self.flag_increment == 0:
            self.v += 1
        else:
            self.v += 32

    def write_dma(self, value: np.uint8) -> None:
        """
        $4014 (OAMDMA - write): This port is located on the CPU. Writing $XX 
        will upload 256 bytes of data from CPU page $XX00-$XXFF to the 
        internal PPU OAM.
        :param value: byte
        """
        from ..main import Manager
        memory = Manager.memory
        cpu = Manager.cpu
        address = np.uint8(np.uint16(value) << 8)
        for i in range(256):
            self.oam_data[self.oam_address] = memory.read(address)
            self.oam_address += 1
            address += 1
        cpu.stall += 513
        if cpu.cycles % 2 == 1:
            cpu.stall += 1

    def nmi_change(self) -> None:
        """
        Changes the NMI interrupt values.
        """
        nmi = self.nmi_output and self.nmi_occurred
        if nmi and not self.nmi_previous:  # bugfix taken from fogleman's code
            self.nmi_delay = 15
        self.nmi_previous = nmi

    @staticmethod
    def trigger_nmi() -> None:
        from ..main import Manager
        cpu = Manager.cpu
        cpu.trigger_interrupt(cpu.interrupts['NMI'])

    def tick(self) -> None:
        """
        Updates the cycle, scanline and frame counters.
        """
        if self.nmi_delay > 0:
            self.nmi_delay -= 1
            if self.nmi_delay == 0 and self.nmi_output and self.nmi_occurred:
                self.trigger_nmi()
        if (self.flag_show_background != 0) or (self.flag_show_sprites != 0):
            if self.f == 1 and self.scanline == 261 and self.cycle == 339:
                self.cycle = 0
                self.scanline = 0
                self.frame += 1
                self.f ^= 1
                return
        self.cycle += 1
        if self.cycle > 340:
            self.cycle = 0
            self.scanline += 1
            if self.scanline > 261:
                self.scanline = 0
                self.frame += 1
                self.f ^= 1

    def step(self) -> None:
        """
        Executes a PPU cycle.
        """
        self.tick()
        rendering_enabled = self.flag_show_background != 0 \
                            or self.flag_show_sprites != 0
        pre_line = self.scanline == 261
        visible_line = self.scanline < 240
        render_line = pre_line or visible_line
        prefetch_cycle = (self.cycle >= 321) and (self.cycle <= 336)
        visible_cycle = (self.cycle >= 1) and (self.cycle <= 256)
        fetch_cycle = prefetch_cycle or visible_cycle

        # background logic
        if rendering_enabled:
            if visible_line and visible_cycle:
                self.render_pixel()
            if render_line and fetch_cycle:
                self.tile_data <<= 4
                # We'll execute different instructions based on each cycle
                # (in loops of 8 cycles)
                cycle = self.cycle % 8
                if cycle == 1:
                    self.fetch_nametable_byte()
                elif cycle == 2:
                    self.fetch_attribute_byte()
                elif cycle == 5:
                    self.fetch_low_tile_byte()
                elif cycle == 7:
                    self.fetch_high_tile_byte()
                elif cycle == 0:
                    self.store_tile_data()

            if pre_line and (self.cycle >= 280) and (self.cycle <= 304):
                self.copy_y()

            if render_line:
                if fetch_cycle and self.cycle % 8 == 0:
                    self.increment_x()
                if self.cycle == 256:
                    self.increment_y()
                elif self.cycle == 257:
                    self.copy_x()

        # sprite logic
        if rendering_enabled:
            if self.cycle == 257:
                if visible_line:
                    self.evaluate_sprites()
                else:
                    self.sprite_count = 0

        if (self.scanline == 241) and (self.cycle == 1):
            self.set_vblank()

        if pre_line and self.cycle == 1:
            self.clear_vblank()
            self.flag_sprite_zero_hit = 0
            self.flag_sprite_overflow = 0

    def clear_vblank(self) -> None:
        """
        Ends the Vertical Blank stage of the frame
        """
        self.nmi_occurred = False
        self.nmi_change()

    def set_vblank(self) -> None:
        """
        Sets the Vertical Blank stage of the frame
        """
        self.front, self.back = self.back, self.front
        self.nmi_occurred = 1
        self.nmi_change()

    def copy_x(self) -> None:
        # hori(v) = hori(t)
        # v: .....F.....EDCBA = t: .....F.....EDCBA
        self.v = (self.v & 0xFBE0) | (self.t & 0x041F)

    def copy_y(self) -> None:
        # vert(v) = vert(t)
        # v:.IHGF.ED CBA..... = t:.IHGF.ED CBA.....
        self.v = (self.v & 0x841F) | (self.t & 0x7BE0)

    def fetch_nametable_byte(self) -> None:
        v = self.v
        address = 0x23C0 | (v & 0x0C00) | ((v >> 4) & 0x38) | ((v >> 2) & 0x07)
        shift = ((v >> 4) & 4) | (v & 2)
        self.attribute_table_byte = (
            (int(self.memory.read(np.uint8(address))) >> shift) & 3
        ) << 2

    def read_palette(self, address: np.uint16) -> np.uint8:
        if address >= 16 and address % 4 == 0:
            address -= 16
        return self.palette_data[address]

    def write_palette(self, address: np.uint16, value: np.uint8):
        if address >= 16 and address % 4 == 0:
            address -= 16
        self.palette_data[address] = value

    def increment_x(self) -> None:
        """
        Increments the v address's horizontal position.
        """
        if self.v & 0x001F == 31:
            self.v &= 0xFFE0
            self.v ^= 0x0400
        else:
            self.v += 1

    def increment_y(self) -> None:
        """
        Increments the v address's vertical position.
        """
        if self.v & 0x7000 != 0x7000:
            self.v += 0x1000
        else:
            self.v &= 0x8FFF
            y = (self.v & 0x03E0) >> 5
            if y == 29:
                y = 0
                self.v ^= 0x0800
            elif y == 31:
                y = 0
            else:
                y += 1

            self.v = (self.v & 0xFC1F) | (y << 5)

