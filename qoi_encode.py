"""
Python script to encode an input PNG image to the QOI format
"""

import argparse
import numpy as np
from PIL import Image, UnidentifiedImageError


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
    run_length = 0

    # process image
    for h in range(height):
        for w in range(width):
            curr = Pixel(pixel_data[h, w, 0],  # r
                         pixel_data[h, w, 1],  # g
                         pixel_data[h, w, 2],  # b
                         pixel_data[h, w, 3])  # a

            index_position = (curr.r * 3 + curr.g * 5 +
                              curr.b * 7 + curr.a * 11) % 64

            # check if max length of runlength is reached
            if run_length == 62:
                bin_data = int("11" + f"{(run_length - 1):06b}", 2)
                output.append(bin_data)
                run_length = 0

            # check for RLE
            if curr == prev:
                # increment runLength and continue processing
                run_length += 1
                continue  # we can safely skip updating prev and pix_array
            else:
                if run_length > 0:
                    # write out current runLength to output and zero it out
                    bin_data = int("11" + f"{(run_length - 1):06b}", 2)
                    output.append(bin_data)
                    run_length = 0

            # check for index
            if curr == pix_array[index_position]:
                bin_data = int("00" + f"{index_position:06b}", 2)
                output.append(bin_data)
            else:
                # check for diff or luma diff
                diff = curr - prev
                if -2 <= diff.r < 2 and -2 <= diff.g < 2 and -2 <= diff.b < 2 and diff.a == 0:
                    dr = diff.r + 2
                    dg = diff.g + 2
                    db = diff.b + 2
                    bin_data = int(
                        "01"+f"{(dr):02b}{(dg):02b}{(db):02b}", 2)
                    output.append(bin_data)
                elif -32 <= diff.g < 32 and -8 <= diff.r - diff.g < 8 and -8 <= diff.b - diff.g < 8 and diff.a == 0:
                    dg = diff.g + 32
                    dr_dg = diff.r - diff.g + 8
                    db_dg = diff.b - diff.g + 8
                    bin_data = int("10"+f"{dg:06b}", 2)
                    output.append(bin_data)
                    bin_data = int(f"{dr_dg:04b}{db_dg:04b}", 2)
                    output.append(bin_data)
                else:
                    if curr.a == prev.a:
                        bin_data = int("11111110", 2)
                        output.append(bin_data)
                        bin_data = int(f"{curr.r:08b}", 2)
                        output.append(bin_data)
                        bin_data = int(f"{curr.g:08b}", 2)
                        output.append(bin_data)
                        bin_data = int(f"{curr.b:08b}", 2)
                        output.append(bin_data)

                    else:
                        bin_data = int("11111111", 2)
                        output.append(bin_data)
                        bin_data = int(f"{curr.r:08b}", 2)
                        output.append(bin_data)
                        bin_data = int(f"{curr.g:08b}", 2)
                        output.append(bin_data)
                        bin_data = int(f"{curr.b:08b}", 2)
                        output.append(bin_data)
                        bin_data = int(f"{curr.a:08b}", 2)
                        output.append(bin_data)

            prev = curr
            pix_array[index_position] = Pixel.fromPixel(curr)

    # check if there is unwritten run length data
    if run_length > 0:
        bin_data = int("11" + f"{(run_length - 1):06b}", 2)
        output.append(bin_data)
        run_length = 0
    return bytes(output)


def write_qoi(filename, data):
    with open(filename, "wb") as outfile:
        outfile.write(data)


def replace_extension(path: str, extension: str):
    old_extension = path.split(".")[-1]
    new_path = path.replace("." + old_extension, "." + extension)
    return new_path


def main():
    parser = argparse.ArgumentParser(
        description="Encode an image to the QOI format.")
    parser.add_argument("filename")
    parser.add_argument(
        "-o", "--output", help="output file name (default: <input_file>.qoi)")
    args = parser.parse_args()

    try:
        im = Image.open(args.filename)
    except FileNotFoundError:
        print(f"Failed to load {args.filename}: file not found.")
        return
    except UnidentifiedImageError:
        print(f"Failed to load {args.filename}: unrecognized format.")
        return

    array = np.array(im)
    height, width, channels = array.shape

    # print(np.zeros((64, 4), dtype="uint8")[63])

    output_data = encode(height, width, channels, array)
    # print(output_data)

    outfile = replace_extension(
        args.filename, "qoi") if not args.output else args.output

    write_qoi(outfile, output_data)

    # rand_image = np.random.randint(low=0, high=255, size=(128, 128, 4))
    # print(rand_image)


if __name__ == "__main__":
    main()
