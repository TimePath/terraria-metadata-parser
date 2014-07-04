# !/usr/bin/env python3
import zlib
import io

from struct import *


class BinaryStream:
    def __init__(self, base_stream):
        self.base_stream = base_stream

    def read_byte(self):
        return self.base_stream.read(1)

    def read_bytes(self, length):
        return self.base_stream.read(length)

    def read_char(self):
        return self.unpack('b')

    def read_uchar(self):
        return self.unpack('B')

    def read_bool(self):
        return self.unpack('?')

    def read_int16(self):
        return self.unpack('h', 2)

    def read_uint16(self):
        return self.unpack('H', 2)

    def read_int32(self):
        return self.unpack('i', 4)

    def read_uint32(self):
        return self.unpack('I', 4)

    def read_string(self):
        length = self.read_uchar()
        return self.unpack(str(length) + 's', length)

    def write_bytes(self, value):
        self.base_stream.write(value)

    def write_char(self, value):
        self.pack('c', value)

    def write_uchar(self, value):
        self.pack('C', value)

    def write_bool(self, value):
        self.pack('?', value)

    def write_int16(self, value):
        self.pack('h', value)

    def write_uint16(self, value):
        self.pack('H', value)

    def write_int32(self, value):
        self.pack('i', value)

    def write_uint32(self, value):
        self.pack('I', value)

    def write_string(self, value):
        length = len(value)
        self.write_uchar(length)
        self.pack(str(length) + 's', value)

    def pack(self, fmt, data):
        return self.write_bytes(pack(fmt, data))

    def unpack(self, fmt, length=1):
        return unpack(fmt, self.read_bytes(length))[0]


def read_bits(count, read):
    arr = []
    b = 0
    bit = 128
    for x in range(count):
        if bit == 128:
            b = read()
            bit = 1
        else:
            bit <<= 1
        arr.append((b & bit) == bit)
    return arr


def read_with_bits(bits, read):
    arr = []
    for i in range(len(bits)):
        if bits[i]:
            arr.append(read())
        else:
            arr.append(1)
    return arr


if __name__ == '__main__':
    with open('/home/andrew/My Games/Terraria/Players/TimePath.bak/1162047362.map', 'rb') as fd:
        stream = BinaryStream(fd)
        curRelease = stream.read_int32()

        print('Release: {0}'.format(curRelease))

        worldName = stream.read_string()
        worldID = stream.read_int32()
        maxTilesY = stream.read_int32()
        maxTilesX = stream.read_int32()

        TileIDCount = stream.read_int16()
        WallIDCount = stream.read_int16()
        maxLiquidTypes = stream.read_int16()

        # maxSkyGradients, maxDirtGradients, maxRockGradients
        num7 = stream.read_int16()
        num8 = stream.read_int16()
        num9 = stream.read_int16()

        print(worldName)
        print(maxTilesY)
        print(maxTilesX)

        array3bits = read_bits(TileIDCount, stream.read_char)
        array4bits = read_bits(WallIDCount, stream.read_char)
        array3 = read_with_bits(array3bits, stream.read_char)
        print('Offset: {0}'.format(stream.base_stream.tell()))
        array4 = read_with_bits(array4bits, stream.read_char)

        num12 = int(sum(array3) + sum(array4) + maxLiquidTypes + num7 + num8 + num9 + 2)
        print('Offset: {0}'.format(stream.base_stream.tell()))
        compressed = stream.read_bytes(None)
        print('Offset: {0}'.format(stream.base_stream.tell()))
        print('Compressed size: {0}'.format(len(compressed)))
        bytestr = zlib.decompress(compressed, -zlib.MAX_WBITS)
        stream = BinaryStream(io.BytesIO(bytestr))

        for l in range(maxTilesY):
            for m in range(maxTilesX):
                b3 = stream.read_char()
                b4 = 0
                if (b3 & 0b1) == 0b1: b4 = stream.read_char()
                b5 = (b3 & 0b1110) >> 1

                flag = {1: True, 2: True, 7: True}.get(b5, False)
                num27 = 0
                if flag:
                    if (b3 & 0b1111) == 0b1111:
                        num27 = stream.read_uint16()
                    else:
                        num27 = stream.read_char()

                light = 255  # light, 255 has special meaning
                if (b3 & 0b100000) == 0b100000:
                    light = stream.read_char()

                n = {1: stream.read_char, 2: stream.read_int16}.get((b3 & 0b11000000) >> 6, lambda: 0)()

                if not b5:
                    m += n
                    continue

                # Other map stuff

                for i in range(n):
                    m += 1
                    if light != 255:
                        light2 = stream.read_char()
