from .base_mapper import BaseMapper
from .mapper2 import Mapper2


def get_mapper(cartridge, mapper_id: int) -> BaseMapper:
    if mapper_id in [0, 2]:
        return Mapper2(cartridge)
