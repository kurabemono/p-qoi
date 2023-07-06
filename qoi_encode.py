"""
Python script to encode an input PNG image to the QOI format
"""

import numpy as np
from PIL import Image


class Pixel:
    def __init__(self, r, g, b, a):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    @classmethod
    def fromPixel(cls, pixel):
        return cls(pixel.r, pixel.g, pixel.b, pixel.a)

    def __eq__(self, other):
        return self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a

    def __sub__(self, other):
        return Pixel(self.r - other.r, self.g - other.g, self.b - other.b, self.a - other.a)


def open_png(filename):
    with Image.open(filename) as im:
        array = np.array(im)
        return array


def encode(height, width, channels, pixel_data):
    # initial encoder values
    prev = Pixel(0, 0, 0, 255)
    pix_array = [Pixel(0, 0, 0, 0) for _ in range(64)]

    for h in height:
        for w in width:
            curr = Pixel(pixel_data[height, width, 0],  # r
                         pixel_data[height, width, 1],  # g
                         pixel_data[height, width, 2],  # b
                         pixel_data[height, width, 3])  # a

            index_position = (curr.r * 3 + curr.g * 5 +
                              curr.b * 7 + curr.a * 11) % 64

            # check for RLE
            if curr == prev:
                pass  # QOI_OP_RUN

            # check for index
            if curr == pix_array[index_position]:
                pass  # QOI_OP_INDEX

            # check for diff or luma
            diff = curr - prev
            if -2 <= diff.r < 2 and -2 <= diff.g < 2 and -2 <= diff.b < 2:
                pass  # QOI_OP_DIFF
            elif -32 <= diff.g < 32 and -8 <= diff.r - diff.g < 8 and -8 <= diff.b - diff.g < 8:
                pass  # QOI_OP_LUMA
            else:
                pass  # QOI_OP_RGB or QOI_OP_RGBA


def write_qoi(filename):
    pass


if __name__ == "__main__":
    array = open_png("testfiles/bricks.png")
    height, width, channels = array.shape
    curr_r, curr_g, curr_b, curr_a = array[0, 0]
    print(curr_g)

    # print(np.zeros((64, 4), dtype="uint8")[63])

    # encode(height, width, channels, array)

    # rand_image = np.random.randint(low=0, high=255, size=(128, 128, 4))
    # print(rand_image)
