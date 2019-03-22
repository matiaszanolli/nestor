import pyglet
import logging
import numpy as np

log = logging.getLogger('logger')


class UI(object):

    def __init__(self, on_draw):
        self.window = pyglet.window.Window(visible=False)
        self.window.set_size(512, 448)
        self.window.on_draw = on_draw
        self.window.set_visible(True)
        self.sprites_to_draw = []

    def clear(self):
        self.window.clear()

    def generate_frame(self):
        from main import Manager
        manager = Manager()
        ppu = manager.ppu
        memory = manager.memory
        log.debug("PPU: Generating new frame...")
        self.sprites_to_draw = []
        ppu.window_frame = pyglet.graphics.Batch()
        background_color = list(ppu.palette_data[memory.read(np.uint16(0x3f00))])
        ppu.background_color = [255, 255, 255]
        background_palette = [ppu.palette_data[x]
                              for x in memory._memory[0x3f01:0x3f10]]
        sprite_palette = [ppu.palette_data[x]
                          for x in memory._memory[0x3f11:0x3f20]]

        background = pyglet.image.ImageData(512, 448, "RGB", bytes(background_color * 512 * 448))
        self.sprites_to_draw.append(pyglet.sprite.Sprite(background, batch=ppu.window_frame))
