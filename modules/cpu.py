import numpy as np
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .memory import Memory


class InstructionMode(object):

    MODE_ABSOLUTE = 0
    MODE_ABSOLUTE_X = 1
    MODE_ABSOLUTE_Y = 2
    MODE_ACCUMULATOR = 3
    MODE_IMMEDIATE = 4
    MODE_IMPLIED = 5
    MODE_INDEXED_INDIRECT = 6
    MODE_INDIRECT = 7
    MODE_INDIRECT_INDEXED = 8
    MODE_RELATIVE = 9
    MODE_ZERO_PAGE = 10
    MODE_ZERO_PAGE_X = 11
    MODE_ZERO_PAGE_Y = 12


class Interrupt(object):

    IRQ = 1
    NMI = 2
    NONE = 0


class StepInfo(object):
    pc = None  # type: np.uint16
    address = None  # type: np.uint8
    mode = None  # type: InstructionMode

    def __init__(self, address: np.uint8, pc: np.uint8, mode: InstructionMode):
        self.address = address
        self.pc = pc
        self.mode = mode


class CPU(object):

    instruction_modes = np.asarray([
        6, 7, 6, 7, 11, 11, 11, 11, 6, 5, 4, 5, 1, 1, 1, 1,
        10, 9, 6, 9, 12, 12, 12, 12, 6, 3, 6, 3, 2, 2, 2, 2,
        1, 7, 6, 7, 11, 11, 11, 11, 6, 5, 4, 5, 1, 1, 1, 1,
        10, 9, 6, 9, 12, 12, 12, 12, 6, 3, 6, 3, 2, 2, 2, 2,
        6, 7, 6, 7, 11, 11, 11, 11, 6, 5, 4, 5, 1, 1, 1, 1,
        10, 9, 6, 9, 12, 12, 12, 12, 6, 3, 6, 3, 2, 2, 2, 2,
        6, 7, 6, 7, 11, 11, 11, 11, 6, 5, 4, 5, 8, 1, 1, 1,
        10, 9, 6, 9, 12, 12, 12, 12, 6, 3, 6, 3, 2, 2, 2, 2,
        5, 7, 5, 7, 11, 11, 11, 11, 6, 5, 6, 5, 1, 1, 1, 1,
        10, 9, 6, 9, 12, 12, 13, 13, 6, 3, 6, 3, 2, 2, 3, 3,
        5, 7, 5, 7, 11, 11, 11, 11, 6, 5, 6, 5, 1, 1, 1, 1,
        10, 9, 6, 9, 12, 12, 13, 13, 6, 3, 6, 3, 2, 2, 3, 3,
        5, 7, 5, 7, 11, 11, 11, 11, 6, 5, 6, 5, 1, 1, 1, 1,
        10, 9, 6, 9, 12, 12, 12, 12, 6, 3, 6, 3, 2, 2, 2, 2,
        5, 7, 5, 7, 11, 11, 11, 11, 6, 5, 6, 5, 1, 1, 1, 1,
        10, 9, 6, 9, 12, 12, 12, 12, 6, 3, 6, 3, 2, 2, 2, 2,
    ])
    instruction_sizes = np.asarray([
        1, 2, 0, 0, 2, 2, 2, 0, 1, 2, 1, 0, 3, 3, 3, 0,
        2, 2, 0, 0, 2, 2, 2, 0, 1, 3, 1, 0, 3, 3, 3, 0,
        3, 2, 0, 0, 2, 2, 2, 0, 1, 2, 1, 0, 3, 3, 3, 0,
        2, 2, 0, 0, 2, 2, 2, 0, 1, 3, 1, 0, 3, 3, 3, 0,
        1, 2, 0, 0, 2, 2, 2, 0, 1, 2, 1, 0, 3, 3, 3, 0,
        2, 2, 0, 0, 2, 2, 2, 0, 1, 3, 1, 0, 3, 3, 3, 0,
        1, 2, 0, 0, 2, 2, 2, 0, 1, 2, 1, 0, 3, 3, 3, 0,
        2, 2, 0, 0, 2, 2, 2, 0, 1, 3, 1, 0, 3, 3, 3, 0,
        2, 2, 0, 0, 2, 2, 2, 0, 1, 0, 1, 0, 3, 3, 3, 0,
        2, 2, 0, 0, 2, 2, 2, 0, 1, 3, 1, 0, 0, 3, 0, 0,
        2, 2, 2, 0, 2, 2, 2, 0, 1, 2, 1, 0, 3, 3, 3, 0,
        2, 2, 0, 0, 2, 2, 2, 0, 1, 3, 1, 0, 3, 3, 3, 0,
        2, 2, 0, 0, 2, 2, 2, 0, 1, 2, 1, 0, 3, 3, 3, 0,
        2, 2, 0, 0, 2, 2, 2, 0, 1, 3, 1, 0, 3, 3, 3, 0,
        2, 2, 0, 0, 2, 2, 2, 0, 1, 2, 1, 0, 3, 3, 3, 0,
        2, 2, 0, 0, 2, 2, 2, 0, 1, 3, 1, 0, 3, 3, 3, 0,
    ])
    instruction_cycles = np.asarray([
        7, 6, 2, 8, 3, 3, 5, 5, 3, 2, 2, 2, 4, 4, 6, 6,
        2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7,
        6, 6, 2, 8, 3, 3, 5, 5, 4, 2, 2, 2, 4, 4, 6, 6,
        2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7,
        6, 6, 2, 8, 3, 3, 5, 5, 3, 2, 2, 2, 3, 4, 6, 6,
        2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7,
        6, 6, 2, 8, 3, 3, 5, 5, 4, 2, 2, 2, 5, 4, 6, 6,
        2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7,
        2, 6, 2, 6, 3, 3, 3, 3, 2, 2, 2, 2, 4, 4, 4, 4,
        2, 6, 2, 6, 4, 4, 4, 4, 2, 5, 2, 5, 5, 5, 5, 5,
        2, 6, 2, 6, 3, 3, 3, 3, 2, 2, 2, 2, 4, 4, 4, 4,
        2, 5, 2, 5, 4, 4, 4, 4, 2, 4, 2, 4, 4, 4, 4, 4,
        2, 6, 2, 8, 3, 3, 5, 5, 2, 2, 2, 2, 4, 4, 6, 6,
        2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7,
        2, 6, 2, 8, 3, 3, 5, 5, 2, 2, 2, 2, 4, 4, 6, 6,
        2, 5, 2, 8, 4, 4, 6, 6, 2, 4, 2, 7, 4, 4, 7, 7,
    ])
    instruction_page_cycles = np.asarray([
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 1, 1,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0,
    ])
    instruction_names = np.asarray([
        'BRK', 'ORA', 'KIL', 'SLO', 'NOP', 'ORA', 'ASL', 'SLO',
        'PHP', 'ORA', 'ASL', 'ANC', 'NOP', 'ORA', 'ASL', 'SLO',
        'BPL', 'ORA', 'KIL', 'SLO', 'NOP', 'ORA', 'ASL', 'SLO',
        'CLC', 'ORA', 'NOP', 'SLO', 'NOP', 'ORA', 'ASL', 'SLO',
        'JSR', '_AND', 'KIL', 'RLA', 'BIT', '_AND', 'ROL', 'RLA',
        'PLP', '_AND', 'ROL', 'ANC', 'BIT', '_AND', 'ROL', 'RLA',
        'BMI', '_AND', 'KIL', 'RLA', 'NOP', '_AND', 'ROL', 'RLA',
        'SEC', '_AND', 'NOP', 'RLA', 'NOP', '_AND', 'ROL', 'RLA',
        'RTI', 'EOR', 'KIL', 'SRE', 'NOP', 'EOR', 'LSR', 'SRE',
        'PHA', 'EOR', 'LSR', 'ALR', 'JMP', 'EOR', 'LSR', 'SRE',
        'BVC', 'EOR', 'KIL', 'SRE', 'NOP', 'EOR', 'LSR', 'SRE',
        'CLI', 'EOR', 'NOP', 'SRE', 'NOP', 'EOR', 'LSR', 'SRE',
        'RTS', 'ADC', 'KIL', 'RRA', 'NOP', 'ADC', 'ROR', 'RRA',
        'PLA', 'ADC', 'ROR', 'ARR', 'JMP', 'ADC', 'ROR', 'RRA',
        'BVS', 'ADC', 'KIL', 'RRA', 'NOP', 'ADC', 'ROR', 'RRA',
        'SEI', 'ADC', 'NOP', 'RRA', 'NOP', 'ADC', 'ROR', 'RRA',
        'NOP', 'STA', 'NOP', 'SAX', 'STY', 'STA', 'STX', 'SAX',
        'DEY', 'NOP', 'TXA', 'XAA', 'STY', 'STA', 'STX', 'SAX',
        'BCC', 'STA', 'KIL', 'AHX', 'STY', 'STA', 'STX', 'SAX',
        'TYA', 'STA', 'TXS', 'TAS', 'SHY', 'STA', 'SHX', 'AHX',
        'LDY', 'LDA', 'LDX', 'LAX', 'LDY', 'LDA', 'LDX', 'LAX',
        'TAY', 'LDA', 'TAX', 'LAX', 'LDY', 'LDA', 'LDX', 'LAX',
        'BCS', 'LDA', 'KIL', 'LAX', 'LDY', 'LDA', 'LDX', 'LAX',
        'CLV', 'LDA', 'TSX', 'LAS', 'LDY', 'LDA', 'LDX', 'LAX',
        'CPY', 'CMP', 'NOP', 'DCP', 'CPY', 'CMP', 'DEC', 'DCP',
        'INY', 'CMP', 'DEX', 'AXS', 'CPY', 'CMP', 'DEC', 'DCP',
        'BNE', 'CMP', 'KIL', 'DCP', 'NOP', 'CMP', 'DEC', 'DCP',
        'CLD', 'CMP', 'NOP', 'DCP', 'NOP', 'CMP', 'DEC', 'DCP',
        'CPX', 'SBC', 'NOP', 'ISC', 'CPX', 'SBC', 'INC', 'ISC',
        'INX', 'SBC', 'NOP', 'SBC', 'CPX', 'SBC', 'INC', 'ISC',
        'BEQ', 'SBC', 'KIL', 'ISC', 'NOP', 'SBC', 'INC', 'ISC',
        'SED', 'SBC', 'NOP', 'ISC', 'NOP', 'SBC', 'INC', 'ISC',
    ])

    frequency = 1789773

    cycles = 0  # type: np.uint64
    pc = None  # program counter, stores the next instruction
    sp: np.uint16 = np.uint16(0xFD)  # stack pointer (documented initial state)
    a: np.uint8 = np.uint8(0)  # accumulator
    x: np.uint8 = np.uint8(0)  # X register
    y: np.uint8 = np.uint8(0)  # Y register
    c: np.uint8 = np.uint8(0)  # carry flag
    z: np.uint8 = np.uint8(0)  # zero flag
    i: np.uint8 = np.uint8(0)  # interrupt disable flag
    d: np.uint8 = np.uint8(0)  # decimal mode flag
    b: np.uint8 = np.uint8(0)  # break command flag
    u: np.uint8 = np.uint8(0)  # unused flag
    v: np.uint8 = np.uint8(0)  # overflow flag
    n: np.uint8 = np.uint8(0)  # negative flag
    interrupt = Interrupt.NONE  # interrupt type to perform
    stall = 0  # number of cycles to stall
    table = []
    memory = None  # type: 'Memory'

    def __init__(self, memory: 'Memory'):
        self.memory = memory

    def reset(self) -> None:
        self.pc = self.memory.read(np.uint8(0xFFFC))
        self.sp = np.uint16(0xFD)
        self.set_flags(0x24)

    def run_instruction(self, inst, **kwargs):
        if inst not in self.instruction_names:
            raise Exception('Invalid instruction!')
        getattr(self, inst.lower())(**kwargs)

    def step(self):
        if self.cycles > 93025:
            print('debug!')
        if self.stall:
            self.stall -= 1
            return 1

        # Handle interrupts
        if self.interrupt == Interrupt.NMI:
            self.nmi()
        elif self.interrupt == Interrupt.IRQ:
            self.irq()
        self.interrupt = Interrupt.NONE

        page_crossed = False
        address = None

        cycles = self.cycles

        # Get the opcode from the program counter, and its instruction mode
        opcode = self.memory.read(self.pc)
        print(f'opcode: {opcode}')
        if int(opcode) >= self.instruction_modes.size:
            print('coso')
        mode = self.instruction_modes[opcode]

        # According to the given instruction's mode, we define which address to
        # send to its handler
        if mode == InstructionMode.MODE_ABSOLUTE:
            address = self.memory.read16(self.pc + 1)
        elif mode == InstructionMode.MODE_ABSOLUTE_X:
            address = self.memory.read16(self.pc + 1) + np.uint16(self.x)
            page_crossed = self.pages_differ(address - np.uint16(self.x),
                                             address)
        elif mode == InstructionMode.MODE_ABSOLUTE_Y:
            address = self.memory.read16(self.pc + 1) + np.uint16(self.y)
            page_crossed = self.pages_differ(address - np.uint16(self.y),
                                             address)
        elif mode == InstructionMode.MODE_ACCUMULATOR:
            address = 0
        elif mode == InstructionMode.MODE_IMMEDIATE:
            address = self.pc + 1
        elif mode == InstructionMode.MODE_IMPLIED:
            address = 0
        elif mode == InstructionMode.MODE_INDEXED_INDIRECT:
            address = self.memory.read16bug(np.uint16(self.memory.read(
                self.pc + 1) + self.x))
        elif mode == InstructionMode.MODE_INDIRECT:
            address = self.memory.read16bug(self.memory.read16(self.pc + 1))
        elif mode == InstructionMode.MODE_INDIRECT_INDEXED:
            address = self.memory.read16bug(np.uint16(self.memory.read(
                self.pc + 1))) + np.uint16(self.y)
            page_crossed = self.pages_differ(address - np.uint16(self.y),
                                             address)
        elif mode == InstructionMode.MODE_RELATIVE:
            offset = np.add(np.int16(self.memory.read(self.pc + 1)),
                            np.uint16(self.y))

            if offset < 0x80:
                address = self.pc + 2 + offset
            else:
                address = self.pc + 2 + offset - 0x100
        elif mode == InstructionMode.MODE_ZERO_PAGE:
            address = np.uint16(self.memory.read(self.pc + 1))
        elif mode == InstructionMode.MODE_ZERO_PAGE_X:
            address = np.uint16(self.memory.read(self.pc + 1) + self.x)
        elif mode == InstructionMode.MODE_ZERO_PAGE_Y:
            address = np.uint16(self.memory.read(self.pc + 1) + self.y)

        self.pc += np.uint16(self.instruction_sizes[opcode])
        self.cycles += np.uint64(self.instruction_cycles[opcode])

        if page_crossed:
            self.cycles += np.uint64(self.instruction_page_cycles[opcode])

        info = StepInfo(address, self.pc, mode)
        opcode_name = self.instruction_names[opcode].lower()

        # Execute the operation
        opcode = getattr(self, opcode_name, None)
        if opcode:
            opcode(info)
            print('Executing opcode: ' + opcode_name)
            print('address: ' + str(hex(address)))
            print('pc: ' + str(hex(self.pc)))

        print(f'cycles: {self.cycles}')
        return int(self.cycles - cycles)

    def set_n(self, value: np.uint8):
        """
        Sets the negative flag if the argument is negative (high bit is set)
        [in 8-bit signed integers, any value > 128 is treated as negative]
        :param value: an 8-bit value
        """
        self.n = np.uint8(1 if value & 0x80 != 0 else 0)

    def set_z(self, value: np.uint8):
        """
        Sets the zero flag if the provided value is zero.
        :param value: byte
        """
        self.z = np.uint8(1 if value == 0 else 0)

    def set_zn(self, value: np.uint8):
        """
        Check the value and set the negative or zero flags if needed.
        :param value: byte
        """
        self.set_z(value)
        self.set_n(value)

    def set_pc(self, info: StepInfo) -> None:
        """
        Redirects the program counter to a new memory address, taking the
        required CPU cycles.
        :param info: a StepInfo object
        """
        self.pc = info.address
        self.add_branch_cycles(info)

    def stack_push(self, value: np.uint8) -> None:
        self.sp -= 1
        self.memory.write(np.uint16(0x100 | np.uint16(self.sp)), value)

    def stack_pull(self) -> np.uint8:
        self.sp += 1
        val = self.memory.read(0x100 + self.sp)
        return val

    def stack_push16(self, value: np.uint16):
        """
        Pushes two bytes into the stack.
        :param value: 16-bit integer
        """
        hi = value >> 8  # takes the upper byte
        lo = value & 0xFF  # lower byte
        self.stack_push(hi)
        self.stack_push(lo)

    def stack_pull16(self) -> np.uint16:
        """
        Pulls two bytes from the stack.
        """
        lo = self.stack_pull()
        hi = self.stack_pull()
        return hi << 8 | lo

    def flags(self):
        flags = 0
        flags = flags | self.c << 0
        flags = flags | self.z << 1
        flags = flags | self.i << 2
        flags = flags | self.d << 3
        flags = flags | self.b << 4
        flags = flags | self.u << 5
        flags = flags | self.v << 6
        flags = flags | self.n << 7
        return flags

    def set_flags(self, flags):
        self.c = (flags >> 0) & 1
        self.z = (flags >> 1) & 1
        self.i = (flags >> 2) & 1
        self.d = (flags >> 3) & 1
        self.b = (flags >> 4) & 1
        self.u = (flags >> 5) & 1
        self.v = (flags >> 6) & 1
        self.n = (flags >> 7) & 1

    @staticmethod
    def pages_differ(a, b):
        """
        Returns true if the two addresses reference different pages.
        :param a: memory address 
        :param b: memory address
        :return: bool
        """
        return a & 0xFF00 != b & 0xFF00

    def add_branch_cycles(self, info: StepInfo) -> None:
        """
        Adds a cycle for taking a branch and adds another cycle if the branch 
        jumps to a new page.
        :param info: a StepInfo object
        """
        self.cycles += 1
        if self.pages_differ(info.pc, info.address):
            self.cycles += 1

    def compare(self, a, b):
        """
        Compares two bytes, setting the carry flag if a is bigger or equal to b
        and setting the Z and N flags according to their difference.
        :param a: byte
        :param b: byte
        """
        self.set_zn(a - b)
        self.c = np.uint8(1 if a >= b else 0)

    def nmi(self):
        """
        Non maskable interrupt
        """
        self.stack_push(self.pc)
        self.php(None)
        self.pc = self.memory.read16(np.uint16(0xFFFA))
        self.i = np.uint8(1)
        # The NES has an interrupt latency of 7 cycles, which means it takes 7
        # CPU cycles to begin executing the interrupt handler
        self.cycles += 7

    def irq(self):
        """
        IRQ interrupt
        """
        self.stack_push(self.pc)
        self.php(None)
        self.pc = self.memory.read16(np.uint16(0xFFFE))
        self.i = np.uint8(1)
        self.cycles += 7

    def adc(self, info: StepInfo) -> None:
        """
        ADC - Add with Carry
        :param info: 
        :return: 
        """
        a = self.a  # accumulator
        b = self.memory.read(info.address)  # memory address input
        c = self.c  # carry flag

        self.a = a + b + c
        self.set_zn(self.a)

        # Step 1: check for carry
        self.c = np.uint8(1 if int(a) + int(b) + int(c) > 0xFF else 0)

        # Step 2: check for overflow
        if (a ^ b) & 0x80 == 0 and (a ^ self.a) & 0x80 != 0:
            self.v = np.uint8(1)
        else:
            self.v = np.uint8(0)

    def _and(self, info: StepInfo) -> None:
        """
        Makes a logical AND between an address and the accumulator
        :param info: a StepInfo object
        """
        self.a = self.a & self.memory.read(info.address)
        self.set_zn(self.a)

    def asl(self, info: StepInfo) -> None:
        """
        ASL: Arithmetic shift - left
        :param info: a StepInfo object
        """
        if info.mode == InstructionMode.MODE_ACCUMULATOR:
            self.c = (self.a << 7) & 1
            self.a = self.a << 1
            self.set_zn(self.a)
        else:
            value = self.memory.read(info.address)
            self.c = (value << 7) & 1
            value = value << 1
            self.memory.write(info.address, value)
            self.set_zn(value)

    def bcc(self, info: StepInfo) -> None:
        """
        BCC (Branch if Carry Clear): If the C flag is clear, redirects the 
        program counter to a given address.
        :param info: a StepInfo object
        """
        if self.c == 0:
            self.set_pc(info)

    def bcs(self, info: StepInfo) -> None:
        """
        BCS (Branch if Carry Set): If the C flag is set, redirects the program
        counter to a given address.
        :param info: a StepInfo object
        """
        if self.c != 0:
            self.set_pc(info)

    def beq(self, info: StepInfo) -> None:
        """
        BEQ (Branch if EQual): If the zero flag is set, redirects the program
        counter to a given address.
        :param info: a StepInfo object
        """
        if self.z != 0:
            self.set_pc(info)

    def bit(self, info: StepInfo) -> None:
        """
        BIT (Bit test): performs a logical AND between the accumulator and a 
        memory address (as well as updating the negative and overflow flags 
        with bits 7 and 6 respectively from the memory location).
        :param info: a StepInfo object
        """
        value = self.memory.read(info.address)
        self.v = (value >> 6) & 1
        self.set_z(value & self.a)
        self.set_n(value)

    def bmi(self, info: StepInfo) -> None:
        """
        BMI (Branch if MInus): If the negative flag is set, redirects the 
        program counter to a given address.
        :param info: a StepInfo object
        """
        if self.n != 0:
            self.set_pc(info)

    def bne(self, info: StepInfo) -> None:
        """
        BEQ (Branch if Not Equal): If the zero flag is clear, redirects the 
        program counter to a given address.
        :param info: a StepInfo object
        """
        if self.z == 0:
            self.set_pc(info)

    def bpl(self, info: StepInfo) -> None:
        """
        BMI (Branch on PLus): If the negative flag is clear, redirects the 
        program counter to a given address.
        :param info: a StepInfo object
        """
        if self.n == 0:
            self.set_pc(info)

    def brk(self, info: StepInfo) -> None:
        """
        BRK (BReaK): Force interrupt
        :param info: 
        :return: 
        """
        self.stack_push16(self.pc)
        self.php(info)
        self.sei(info)
        self.pc = self.memory.read16(np.uint16(0xFFFE))

    def bvc(self, info: StepInfo) -> None:
        """
        BVC (Branch if oVerflow Clear): If the V flag is clear, redirects the 
        program counter to a given address.
        :param info: a StepInfo object
        """
        if self.v == 0:
            self.set_pc(info)

    def bvs(self, info: StepInfo) -> None:
        """
        BVS (Branch if oVerflow Set): If the V flag is set, redirects the 
        program counter to a given address.
        :param info: a StepInfo object
        """
        if self.v != 0:
            self.set_pc(info)

    def clc(self, info: StepInfo) -> None:
        """
        CLC (CLear the Carry flag).
        :param info: a StepInfo object.
        """
        self.c = np.uint8(0)

    def cld(self, info: StepInfo) -> None:
        """
        CLD (CLear the Decimal mode).
        :param info: a StepInfo object.
        """
        self.d = np.uint8(0)

    def cli(self, info: StepInfo) -> None:
        """
        CLD (CLear the Interrupt disable).
        :param info: a StepInfo object.
        """
        self.i = np.uint8(0)

    def clv(self, info: StepInfo) -> None:
        """
        CLV (CLear the oVerflow flag).
        :param info: a StepInfo object.
        """
        self.v = np.uint8(0)

    def cmp(self, info: StepInfo) -> None:
        """
        CMP (CoMPare): Compares the accumulator with a given address.
        :param info: a StepInfo object.
        """
        value = self.memory.read(info.address)
        self.compare(self.a, value)

    def cpx(self, info: StepInfo) -> None:
        """
        CPX (ComPare with X): Compares the X register with a given address.
        :param info: a StepInfo object.
        """
        value = self.memory.read(info.address)
        self.compare(self.x, value)

    def cpy(self, info: StepInfo) -> None:
        """
        CPY (ComPare with Y): Compares the Y register with a given address.
        :param info: a StepInfo object.
        """
        value = self.memory.read(info.address)
        self.compare(self.y, value)

    def dec(self, info: StepInfo) -> None:
        """
        DEC (DECrement memory): Subtracts one -1- from the contents of a given 
        memory address.
        :param info: a StepInfo object.
        """
        value = self.memory.read(info.address) - 1
        self.memory.write(info.address, value)
        self.set_zn(value)

    def dex(self, info: StepInfo) -> None:
        """
        DEX (DEcrement X): Subtracts one -1- from the contents of X register.
        :param info: a StepInfo object.
        """
        self.x -= 1
        self.set_zn(self.x)

    def dey(self, info: StepInfo) -> None:
        """
        DEY (DEcrement Y): Subtracts one -1- from the contents of Y register.
        :param info: a StepInfo object.
        """
        self.y -= 1
        self.set_zn(self.y)

    def eor(self, info: StepInfo) -> None:
        """
        EOR: Performs an exclusive OR between an address contents and the 
        accumulator.
        :param info: a StepInfo object.
        """
        self.a = self.a ^ self.memory.read(info.address)
        self.set_zn(self.a)

    def inc(self, info: StepInfo) -> None:
        """
        DEC (INCrement memory): Adds one -1- to the contents of a given 
        memory address.
        :param info: a StepInfo object.
        """
        value = self.memory.read(info.address) + 1
        self.memory.write(info.address, value)
        self.set_zn(value)

    def inx(self, info: StepInfo) -> None:
        """
        INX (INcrement X): Adds one -1- to the contents of X register.
        :param info: a StepInfo object.
        """
        self.x += 1
        self.set_zn(self.x)

    def iny(self, info: StepInfo) -> None:
        """
        INY (INcrement Y): Adds one -1- to the contents of Y register.
        :param info: a StepInfo object.
        """
        self.y += 1
        self.set_zn(self.y)

    def jmp(self, info: StepInfo) -> None:
        """
        JMP (JuMP): Moves the program counter to a given memory address.
        :param info: a StepInfo object.
        """
        self.pc = info.address

    def jsr(self, info: StepInfo) -> None:
        """
        JSR (Jump to Sub Routine): pushes the address-1 of the next operation 
        on to the stack before transferring program control to the following 
        address.
        :param info: a StepInfo object.
        """
        self.stack_push16(self.pc - 1)
        self.pc = info.address

    def lda(self, info: StepInfo) -> None:
        """
        LDA (LoaD Accumulator): Loads the accumulator with the content of a
        memory address.
        :param info: a StepInfo object.
        """
        self.a = self.memory.read(info.address)
        self.set_zn(self.a)

    def ldx(self, info: StepInfo) -> None:
        """
        LDX (LoaD into X): Loads the X register with the content of a
        memory address.
        :param info: a StepInfo object.
        """
        self.x = self.memory.read(info.address)
        self.set_zn(self.x)

    def ldy(self, info: StepInfo) -> None:
        """
        LDY (LoaD into Y): Loads the accumulator with the content of a
        memory address.
        :param info: a StepInfo object.
        """
        self.y = self.memory.read(info.address)
        self.set_zn(self.y)

    def lsr(self, info: StepInfo) -> None:
        """
        LSR: Logical Shift - Right
        :param info: a StepInfo object
        """
        if info.mode == InstructionMode.MODE_ACCUMULATOR:
            self.c = self.a & 1
            self.a = self.a >> 1
            self.set_zn(self.a)
        else:
            value = self.memory.read(info.address)
            self.c = value & 1
            value >>= 1
            self.memory.write(info.address, value)
            self.set_zn(value)

    def nop(self, info: StepInfo) -> None:
        """
        NOP (No OPeration)
        :param info: a StepInfo object
        """
        pass

    def ora(self, info: StepInfo) -> None:
        """
        ORA (logical inclusive OR on Accumulator)
        :param info: a StepInfo object 
        """
        self.a = self.a | self.memory.read(info.address)
        self.set_zn(self.a)

    def pha(self, info: StepInfo) -> None:
        """
        PHA (PuSH accumulator): Pushes the accumulator value to the stack
        :param info: a StepInfo object 
        """
        self.stack_push(self.a)

    def php(self, info: StepInfo) -> None:
        """
        PHP (PusH Processor status): Pushes all flags to the stack.
        :param info: a StepInfo object.
        """
        self.stack_push(self.flags() | 0x10)

    def pla(self, info: StepInfo) -> None:
        """
        PLA (PuLl into accumulator): Pulls the accumulator value to 
        :param info: a StepInfo object 
        """
        self.a = self.stack_pull()
        self.set_zn(self.a)

    def plp(self, info: StepInfo) -> None:
        """
        PLP (PuLl Processor status): Pulls all flags from the stack.
        :param info: a StepInfo object 
        """
        self.set_flags(self.stack_pull() & 0xEF | 0x20)

    def rol(self, info: StepInfo) -> None:
        """
        ROL (ROtate Left): shifts all bits left one position. The Carry is 
        shifted into bit 0 and the original bit 7 is shifted into the Carry.
        :param info: a StepInfo object 
        """
        c = self.c
        if info.mode == InstructionMode.MODE_ACCUMULATOR:
            self.c = (self.a >> 7) & 1
            self.a = (self.a << 1) & c
            self.set_zn(self.a)
        else:
            value = self.memory.read(info.address)
            self.c = (value >> 7) & 1
            value = (value << 1) & c
            self.memory.write(info.address, value)
            self.set_zn(value)

    def ror(self, info: StepInfo) -> None:
        """
        ROR (ROtate Right): shifts all bits right one position. The Carry is 
        shifted into bit 7 and the original bit 0 is shifted into the Carry.
        :param info: a StepInfo object 
        """
        c = self.c
        if info.mode == InstructionMode.MODE_ACCUMULATOR:
            self.c = self.a & 1
            self.a = (self.a >> 1) | (c << 7)
            self.set_zn(self.a)
        else:
            value = self.memory.read(info.address)
            self.c = value & 1
            value = (value >> 1) | (c << 7)
            self.memory.write(info.address, value)
            self.set_zn(value)

    def rti(self, info: StepInfo) -> None:
        """
        RTI (ReTurn from Interrupt): retrieves the flags and the Program 
        Counter from the stack (in that order).
        :param info: a StepInfo object 
        """
        self.set_flags(self.stack_pull() & 0xEF | 0x20)
        self.pc = self.stack_pull16()

    def rts(self, info: StepInfo) -> None:
        """
        RTS (ReTurn from Subroutine): pulls the top two bytes off the stack 
        (low byte first) and transfers program control to that address + 1.
        :param info: a StepInfo object 
        """
        self.pc = self.stack_pull16() + 1

    def sbc(self, info: StepInfo) -> None:
        """
        SBC (SuBstract with Carry)
        :param info: a StepInfo object 
        """
        a = self.a
        b = self.memory.read(info.address)
        c = self.c
        self.a = a - b - (1 - c)
        self.set_zn(self.a)
        self.c = np.uint8(1 if int(a) - int(b) - int(1 - c) >= 0 else 0)
        self.v = np.uint8(1 if (a ^ b) & 0x80 != 0 and (a ^ self.a) & 0x80 != 0 else 0)

    def sec(self, info: StepInfo) -> None:
        """
        SEC (SEt Carry flag)
        :param info: a StepInfo object 
        """
        self.c = np.uint8(1)

    def sed(self, info: StepInfo) -> None:
        """
        SED (SEt Decimal flag)
        :param info: a StepInfo object 
        """
        self.d = np.uint8(1)

    def sei(self, info: StepInfo) -> None:
        """
        SEI (SEt Interrupt disable)
        :param info: a StepInfo object 
        """
        self.i = np.uint8(1)

    def sta(self, info: StepInfo) -> None:
        """
        STA (STore Accumulator): Stores the accumulator value in a given
        memory address.
        :param info: a StepInfo object 
        """
        self.memory.write(info.address, self.a)

    def stx(self, info: StepInfo) -> None:
        """
        STX (STore register X): Stores the X register value in a given
        memory address.
        :param info: a StepInfo object 
        """
        self.memory.write(info.address, self.x)

    def sty(self, info: StepInfo) -> None:
        """
        STY (STore register Y): Stores the Y register value in a given
        memory address.
        :param info: a StepInfo object 
        """
        self.memory.write(info.address, self.y)

    def tax(self, info: StepInfo) -> None:
        """
        TAX (Transfer accumulator to X): Stores the accumulator value in the
        X register.
        :param info: a StepInfo object 
        """
        self.x = self.a
        self.set_zn(self.x)

    def tay(self, info: StepInfo) -> None:
        """
        TAY (Transfer accumulator to Y): Stores the accumulator value in the
        Y register.
        :param info: a StepInfo object 
        """
        self.y = self.a
        self.set_zn(self.y)

    def tsx(self, info: StepInfo) -> None:
        """
        TSX (Transfer Stack pointer to X): Stores the stack pointer value in 
        the X register.
        :param info: a StepInfo object 
        """
        self.x = self.sp
        self.set_zn(self.x)

    def txa(self, info: StepInfo) -> None:
        """
        TXA (Transfer X to Accumulator): Stores the X register value in 
        the accumulator.
        :param info: a StepInfo object 
        """
        self.a = self.x
        self.set_zn(self.a)

    def txs(self, info: StepInfo) -> None:
        """
        TXS (Transfer X to Stack pointer): Stores the X register value in 
        the stack pointer.
        :param info: a StepInfo object 
        """
        self.sp = self.x

    def tya(self, info: StepInfo) -> None:
        """
        TYA (Transfer Y to Accumulator): Stores the Y register value in 
        the accumulator.
        :param info: a StepInfo object 
        """
        self.a = self.y
        self.set_zn(self.a)
