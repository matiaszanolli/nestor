import numpy as np


# I/O Handling logic.
class IO(object):

    def __init__(self):
        self.gamepad_bits = np.ndarray(2, dtype=np.uint8)
        self.strobe = False

    def read_state(self, port: int) -> np.uint8:
        """
        Reads the current state from the selected I/O port.
        """
        return np.uint8(0)

    def write_strobe(self, value: np.uint8) -> np.uint8:
        """
        Even when this is implemented will return zero, since all instructions need to return something.
        """
        return np.uint8(0)
