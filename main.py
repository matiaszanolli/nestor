"""
NEStor: an attempt to understand emulation by Matias Zanolli
Heavily based on https://github.com/fogleman/nes
Also took some elements from https://github.com/makononov/PyNES

It's not a brand new emulator, but more of an attempt to understand how
emulators work internally, in order to have a solid knowledge base before
starting one from scratch.
"""
import pyglet

from modules.cartridge import Cartridge
from modules.apu import APU
from modules.cpu import CPU
from modules.memory import Memory
from modules.ppu import PPU


class Manager(object):

    instance = None  # type: Manager
    memory = Memory()
    counter = 0
    ppu = PPU(memory)
    cpu = CPU(memory)
    apu = APU()
    cartridge = Cartridge

    def __init__(self):
        self.window = pyglet.window.Window(visible=False)
        self.window.set_size(512, 448)
        self.window.on_draw = self.on_draw
        self.window.set_visible(True)

    @classmethod
    def get(cls):
        if not cls.instance:
            cls.instance = Manager()
        return cls.instance

    def on_draw(self):
        self.window.clear()
        self.ppu.frame.draw()

    def tick(self):
        self.counter += 1

    def reset(self):
        self.cpu.reset()


if __name__ == "__main__":
    manager = Manager.get()
    pyglet.app.run()
