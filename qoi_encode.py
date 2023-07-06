"""
Python script to encode an input PNG image to the QOI format
"""

import numpy as np
from PIL import Image


class Pixel:
    def __init__(self, r, g, b, a):
        self.r = int(r)
        self.g = int(g)
        self.b = int(b)
        self.a = int(a)

    @classmethod
    def fromPixel(cls, pixel):
        return cls(pixel.r, pixel.g, pixel.b, pixel.a)

    def __str__(self):
        return f"Pixel ({self.r}, {self.g}, {self.b}, {self.a})"

    def __eq__(self, other):
        return self.r == other.r and self.g == other.g and self.b == other.b and self.a == other.a

    def __sub__(self, other):
        return Pixel(self.r - other.r, self.g - other.g, self.b - other.b, self.a - other.a)


def open_png(filename):
    with Image.open(filename) as im:
        array = np.array(im)
        return array


def encode(height: int, width: int, channels: int, pixel_data):
    output = []  # byte array

    # output header data
    for byte in b"qoif":
        output.append(byte)
    for byte in width.to_bytes(4, byteorder="big"):
        output.append(byte)
    for byte in height.to_bytes(4, byteorder="big"):
        output.append(byte)
    for byte in channels.to_bytes(1, byteorder="big"):
        output.append(byte)
    for byte in int(0).to_bytes(1, byteorder="big"):
        output.append(byte)

    # initial encoder values
    prev = Pixel(0, 0, 0, 255)
    pix_array = [Pixel(0, 0, 0, 0) for _ in range(64)]
    runLength = 0

    for h in range(height):
        for w in range(width):
            curr = Pixel(pixel_data[h, w, 0],  # r
                         pixel_data[h, w, 1],  # g
                         pixel_data[h, w, 2],  # b
                         pixel_data[h, w, 3])  # a

            index_position = (curr.r * 3 + curr.g * 5 +
                              curr.b * 7 + curr.a * 11) % 64

            # print("prev:", prev)
            # print("curr:", curr)

            # check if max length of runlength is reached
            if runLength == 62:
                print("max length of runLength reached")
                bin_data = int("11" + f"{(runLength - 1):06b}", 2)
                print(hex(bin_data), bin(bin_data))
                output.append(bin_data)
                runLength = 0

            # check for RLE
            if curr == prev:
                # increment runLength and continue processing
                # print("curr == prev")
                runLength += 1
                continue  # we can safely skip updating prev and pix_array
            else:
                if runLength > 0:
                    print("run length streak broken")
                    # write out current runLength to output and zero it out
                    bin_data = int("11" + f"{(runLength - 1):06b}", 2)
                    print(hex(bin_data), bin(bin_data))
                    output.append(bin_data)
                    runLength = 0

            # check for index
            if curr == pix_array[index_position]:
                print("curr matches item at pix_array at index:", index_position)
                bin_data = int("00" + f"{index_position:06b}", 2)
                print(hex(bin_data), bin(bin_data))
                output.append(bin_data)
            else:
                # check for diff or luma diff
                diff = curr - prev
                # print("diff:", diff)
                if -2 <= diff.r < 2 and -2 <= diff.g < 2 and -2 <= diff.b < 2 and diff.a == 0:
                    print("rgb diff is within 2 bits and a is equal")
                    dr = diff.r + 2
                    dg = diff.g + 2
                    db = diff.b + 2
                    bin_data = int(
                        "01"+f"{(dr):02b}{(dg):02b}{(db):02b}", 2)
                    print(hex(bin_data), bin(bin_data))
                    output.append(bin_data)
                elif -32 <= diff.g < 32 and -8 <= diff.r - diff.g < 8 and -8 <= diff.b - diff.g < 8 and diff.a == 0:
                    print("luma diff is within bounds")
                    dg = diff.g + 32
                    dr_dg = diff.r - diff.g + 8
                    db_dg = diff.b - diff.g + 8
                    bin_data = int("10"+f"{dg:06b}", 2)
                    print(hex(bin_data), bin(bin_data))
                    output.append(bin_data)
                    bin_data = int(f"{dr_dg:04b}{db_dg:04b}", 2)
                    print(hex(bin_data), bin(bin_data))
                    output.append(bin_data)
                else:
                    if curr.a == prev.a:
                        print("passthrough RGB")
                        bin_data = int("11111110", 2)
                        print(hex(bin_data), bin(bin_data), end=None)
                        output.append(bin_data)
                        bin_data = int(f"{curr.r:08b}", 2)
                        print(hex(bin_data), bin(bin_data), end=None)
                        output.append(bin_data)
                        bin_data = int(f"{curr.g:08b}", 2)
                        print(hex(bin_data), bin(bin_data), end=None)
                        output.append(bin_data)
                        bin_data = int(f"{curr.b:08b}", 2)
                        print(hex(bin_data), bin(bin_data))
                        output.append(bin_data)

                    else:
                        print("passthrough RGBA")
                        bin_data = int("11111111", 2)
                        print(hex(bin_data), bin(bin_data), end=None)
                        output.append(bin_data)
                        bin_data = int(f"{curr.r:08b}", 2)
                        print(hex(bin_data), bin(bin_data), end=None)
                        output.append(bin_data)
                        bin_data = int(f"{curr.g:08b}", 2)
                        print(hex(bin_data), bin(bin_data), end=None)
                        output.append(bin_data)
                        bin_data = int(f"{curr.b:08b}", 2)
                        print(hex(bin_data), bin(bin_data), end=None)
                        output.append(bin_data)
                        bin_data = int(f"{curr.a:08b}", 2)
                        print(hex(bin_data), bin(bin_data), end=None)
                        output.append(bin_data)

            prev = curr
            pix_array[index_position] = Pixel.fromPixel(curr)
    return bytes(output)


def write_qoi(filename, data):
    with open(filename, "wb") as outfile:
        outfile.write(data)


if __name__ == "__main__":
    array = open_png("testfiles/exam.png")
    height, width, channels = array.shape
    curr_r, curr_g, curr_b, curr_a = array[0, 0]

    # print(np.zeros((64, 4), dtype="uint8")[63])

    output = encode(height, width, channels, array)
    print(output)
    write_qoi("testfiles/output.qoi", output)

    # rand_image = np.random.randint(low=0, high=255, size=(128, 128, 4))
    # print(rand_image)
