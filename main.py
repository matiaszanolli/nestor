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

import pyglet

from modules.cartridge import Cartridge
from modules.apu import APU
from modules.cpu import CPU
from modules.memory import Memory
from modules.ppu import PPU
from modules.ui import UI

log = logging.getLogger('logger')


class Manager(object):

    instance = None  # type: Manager
    memory = Memory()  # type: Memory
    counter = 0  # type: int
    ppu = PPU(memory)  # type: PPU
    cpu = CPU(memory)  # type: CPU
    apu = APU()
    cartridge = None  # type: Cartridge
    ui = None  # type: UI

    def __init__(self):
        self.ui = UI(on_draw=self.on_draw)
        parser = argparse.ArgumentParser(
            description="Command line options for NEStor")
        parser.add_argument('romfile', metavar="filename", type=str,
                            help="The ROM file to load")
        args = parser.parse_args()
        self.cartridge = Cartridge(args.romfile)
        self.mapper = self.cartridge.mapper

    @classmethod
    def get(cls):
        if not cls.instance:
            cls.instance = Manager()
        return cls.instance

    def on_draw(self):
        self.ui.clear()
        self.ppu.frame.draw()

    def step(self):
        cpu_cycles = self.cpu.step()
        ppu_cycles = cpu_cycles * 3  # PPU runs at thrice the speed
        for _ in range(ppu_cycles):
            self.ppu.step()
            self.mapper.step()
        for _ in range(cpu_cycles):
            self.apu.step()
        return cpu_cycles

    def reset(self):
        self.cpu.reset()


if __name__ == "__main__":

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    logging.info('Starting...')

    manager = Manager.get()
    manager.reset()
    while True:
        manager.step()

    pyglet.app.run()
