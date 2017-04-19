"""
I have no freaking idea of what I am doing
"""
import numpy as np
import pyglet
from .cpu import CPU
from .apu import APU
from .ppu import PPU
from .memory import Memory
from .cartridge import Cartridge


class Manager(object):

    instance = None  # type: Manager
    memory = Memory()
    counter = 0
    ppu = PPU()
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
        self.PPU.frame.draw()

    def tick(self):
        self.counter += 1

    def reset(self):
        self.cpu.reset()


if __name__ == "__main__":
    manager = Manager.get()
    pyglet.app.run()