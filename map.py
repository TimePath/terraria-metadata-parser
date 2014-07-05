# !/usr/bin/env python3
import zlib
import io
from enum import IntEnum
from struct import *


class BinaryStream:
    def __init__(self, base_stream):
        self.base_stream = base_stream

    def read(self, limit=None):
        return self.base_stream.read(limit)

    def unpack(self, fmt, length=1):
        return unpack(fmt, self.read(length))[0]

    def read_bool(self):
        return self.unpack('?')

    def read_int8(self):
        return self.unpack('b')

    def read_uint8(self):
        return self.unpack('B')

    def read_int16(self):
        return self.unpack('h', 2)

    def read_uint16(self):
        return self.unpack('H', 2)

    def read_int32(self):
        return self.unpack('i', 4)

    def read_uint32(self):
        return self.unpack('I', 4)

    def read_string(self):
        length = self.read_uint8()
        return self.unpack(str(length) + 's', length).decode("utf-8")

    def write(self, value):
        self.base_stream.write(value)

    def pack(self, fmt, data):
        return self.write(pack(fmt, data))

    def write_bool(self, value):
        self.pack('?', value)

    def write_int8(self, value):
        self.pack('c', value)

    def write_uint8(self, value):
        self.pack('C', value)

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
        self.write_uint8(length)
        self.pack(str(length) + 's', value)


class Header(IntEnum):
    Empty = 0
    Tile = 1
    Wall = 2
    Water = 3
    Lava = 4
    Honey = 5
    HeavenAndHell = 6
    Background = 7


def read_bits(count, read_byte):
    arr = []
    byte = 0
    bit = 128
    for i in range(count):
        if bit == 128:
            byte = read_byte()
            bit = 1
        else:
            bit <<= 1
        arr.append((byte & bit) == bit)
    return arr


def read_with_bits(bitfield, read_byte):
    arr = []
    for bit in bitfield:
        if bit:
            arr.append(read_byte())
        else:
            arr.append(1)
    return arr


if __name__ == '__main__':
    tileOptionCounts, wallOptionCounts = [1] * 340, [1] * 172  # TODO
    with open('/home/andrew/My Games/Terraria/Players/TimePath.bak/1162047362.map', 'rb') as fd:
        stream = BinaryStream(fd)
        version = stream.read_int32()

        worldName = stream.read_string()
        worldID = stream.read_int32()
        maxTilesY = stream.read_int32()
        maxTilesX = stream.read_int32()

        tileIDCount = stream.read_int16()
        wallIDCount = stream.read_int16()
        liquidTypes = stream.read_int16()

        skyGradients = stream.read_int16()
        dirtGradients = stream.read_int16()
        rockGradients = stream.read_int16()

        print('''terraria-metadata-parser
Format: {0}
world: {1}
width: {2}
height: {3}'''.format(version, worldName, maxTilesX, maxTilesY))

        maxTileOptionsBits = read_bits(tileIDCount, stream.read_int8)
        maxWallOptionsBits = read_bits(wallIDCount, stream.read_int8)

        maxTileOptions = read_with_bits(maxTileOptionsBits, stream.read_int8)
        maxWallOptions = read_with_bits(maxWallOptionsBits, stream.read_int8)

        typeCount = 2 + sum(maxTileOptions) + sum(maxWallOptions) \
                    + liquidTypes + skyGradients + dirtGradients + rockGradients

        types = [0]
        typesIdx = 1  # index into all known types

        offsetTiles = len(types)
        for i in range(len(tileOptionCounts)):  # for all known tiles
            if i < tileIDCount:  # that this map knows about
                for j in range(tileOptionCounts[i]):  # for every tile option
                    if j < maxTileOptions[i]:  # that this map knows about
                        types.append(typesIdx)  # add a mapping
                    typesIdx += 1
            else:  # skip entirely
                typesIdx += tileOptionCounts[i]

        offsetWalls = len(types)
        for i in range(len(wallOptionCounts)):  # for all known walls
            if i < wallIDCount:  # that this map knows about
                for j in range(wallOptionCounts[i]):  # for every wall option
                    if j < maxWallOptions[i]:  # that this map knows about
                        types.append(typesIdx)  # add a mapping
                    typesIdx += 1
            else:  # skip entirely
                typesIdx += wallOptionCounts[i]

        offsetLiquid = len(types)
        for i in range(liquidTypes):
            types.append(typesIdx)
            typesIdx += 1

        offsetSky = len(types)
        for i in range(skyGradients):
            types.append(typesIdx)
            typesIdx += 1

        offsetDirt = len(types)
        for i in range(dirtGradients):
            types.append(typesIdx)
            typesIdx += 1

        offsetRock = len(types)
        for i in range(rockGradients):
            types.append(typesIdx)
            typesIdx += 1

        # add the last tile to the end?
        num25 = len(types)
        types.append(typesIdx)

        compressed = stream.read()
        bytestr = zlib.decompress(compressed, -zlib.MAX_WBITS)
        stream = BinaryStream(io.BytesIO(bytestr))

        for y in range(maxTilesY):
            xit = iter(range(maxTilesX))
            for x in xit:
                n1 = stream.read_int8()
                n2 = 0
                if (n1 & 0b1) == 0b1:
                    n2 = stream.read_int8()

                layer = (n1 & 0b1110) >> 1

                typeIndex = 0
                if {Header.Tile: True, Header.Wall: True, Header.Background: True}.get(layer, False):
                    if (n1 & 0b10000) == 0b10000:
                        typeIndex = stream.read_uint16()
                    else:
                        typeIndex = stream.read_int8()

                light = 255  # 255 has special meaning
                if (n1 & 0b100000) == 0b100000:
                    light = stream.read_int8()

                remaining = {1: stream.read_uint8, 2: stream.read_uint16}.get((n1 & 0b11000000) >> 6, lambda: 0)()

                if layer == Header.Empty:
                    for _ in range(remaining):
                        next(xit)
                    continue

                worldSurface, rockLayer = y, y  # TODO
                typeIndex += {Header.Tile: lambda: offsetTiles,
                              Header.Wall: lambda: offsetWalls,
                              Header.Water: lambda: offsetLiquid - Header.Water,
                              Header.Lava: lambda: offsetLiquid - Header.Water,
                              Header.Honey: lambda: offsetLiquid - Header.Water,
                              Header.HeavenAndHell: lambda:
                              offsetSky + (skyGradients * (y / worldSurface)) if y < worldSurface
                              else num25 - typeIndex,
                              Header.Background: lambda: offsetDirt if y < rockLayer else offsetRock
                }.get(layer, lambda: 0)()
                color = (n2 >> 1) & 0b11111
                type = types[typeIndex]
                for i in range(remaining):
                    next(xit)
                    if light != 255:
                        light2 = stream.read_int8()
                print(y,x,remaining)
