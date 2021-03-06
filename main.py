"""
NEStor: an attempt to understand emulation by Matias Zanolli
Heavily based on https://github.com/fogleman/nes
Also took some elements from https://github.com/makononov/PyNES

Useful documentation about the NES internals:
http://nesdev.com/NESDoc.pdf
http://nesdev.com/NESTechFAQ.htm
https://medium.com/@fogleman/i-made-an-nes-emulator-here-s-what-i-learned-about-the-original-nintendo-2e078c9b28fe

It's not a brand new emulator, but more of an attempt to understand how
emulators work internally, in order to have a solid knowledge base before
starting one from scratch.
"""
import argparse
import logging
import threading


import pyglet

from modules.memory import Memory

log = logging.getLogger('logger')

lock = threading.Lock()


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class Manager(threading.Thread, metaclass=Singleton):

    def __init__(self) -> None:

        super().__init__()

        from modules.cartridge import Cartridge
        from modules.apu import APU
        from modules.cpu import CPU
        from modules.memory import PPUMemory
        from modules.ppu import PPU
        from modules.ui import UI
        from modules.controller import IO

        self._memory: Memory = Memory()
        self.ppu: PPU = PPU(self.memory)
        self.cpu: CPU = CPU(self.memory)
        self.counter: int = 0
        self.apu: APU = APU()
        self.ui = UI(on_draw=self.on_draw)
        self.io = IO()
        self.ppu_memory = PPUMemory(self)
        parser = argparse.ArgumentParser(
            description="Command line options for NEStor")
        parser.add_argument('romfile', metavar="filename", type=str,
                            help="The ROM file to load")
        args = parser.parse_args()
        self.cartridge = Cartridge(args.romfile)
        self._mapper = self.cartridge.mapper

    def run(self) -> None:
        self.reset()
        while True:
            self.step()

    @property
    def memory(self) -> Memory:
        return getattr(self, '_memory', None)

    @memory.setter
    def memory(self, value) -> None:
        self._memory = value

    @property
    def mapper(self) -> 'BaseMapper':
        return getattr(self, '_mapper', None)

    @mapper.setter
    def mapper(self, value) -> None:
        self._mapper = value

    def on_draw(self) -> None:
        self.ui.clear()
        window_frame = self.ppu.window_frame
        window_frame.draw()

    def step(self) -> int:
        cpu_cycles = self.cpu.step()
        ppu_cycles = cpu_cycles * 3  # PPU runs at thrice the speed
        for _ in range(ppu_cycles):
            self.ppu.step()
            self.mapper.step()
        for _ in range(cpu_cycles):
            self.apu.step()
        return cpu_cycles

    def reset(self) -> None:
        self.cpu.reset()


if __name__ == "__main__":

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    logging.info('Starting...')

    manager = Manager()
    manager.start()

    pyglet.app.run()
