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


log = logging.getLogger('logger')


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


@singleton
class Manager(threading.Thread):

    def __init__(self):
        from modules.cartridge import Cartridge
        from modules.apu import APU
        from modules.cpu import CPU
        from modules.memory import Memory, PPUMemory
        from modules.ppu import PPU
        from modules.ui import UI

        super().__init__()

        self.memory = Memory()  # type: Memory
        self.ppu = PPU(self.memory)  # type: PPU
        self.cpu = CPU(self.memory)  # type: CPU
        self.counter = 0  # type: int
        self.apu = APU()
        self.ui = UI(on_draw=self.on_draw)
        self.ppu_memory = PPUMemory(self)
        parser = argparse.ArgumentParser(
            description="Command line options for NEStor")
        parser.add_argument('romfile', metavar="filename", type=str,
                            help="The ROM file to load")
        args = parser.parse_args()
        self.cartridge = Cartridge(args.romfile)
        self.mapper = self.cartridge.mapper

    def on_draw(self):
        self.ui.clear()
        self.ppu.window_frame.draw()

    def step(self):
        cpu_cycles = self.cpu.step()
        ppu_cycles = cpu_cycles * 3  # PPU runs at thrice the speed
        for _ in range(ppu_cycles):
            self.ppu.step()
            self.mapper.step()
        for _ in range(cpu_cycles):
            self.apu.step()
        self.ui.generate_frame()
        return cpu_cycles

    def run(self):
        self.reset()
        while True:
            self.step()

    def reset(self):
        self.cpu.reset()


if __name__ == "__main__":

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    logging.info('Starting...')

    manager = Manager()
    manager.start()

    pyglet.app.run()
