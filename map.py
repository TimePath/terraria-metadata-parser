import zlib
import io

from struct import *

class BinaryStream:
    def __init__(self, base_stream):
        self.base_stream = base_stream

    def readByte(self):
        return self.base_stream.read(1)

    def readBytes(self, length):
        return self.base_stream.read(length)

    def readChar(self):
        return self.unpack('b')

    def readUChar(self):
        return self.unpack('B')

    def readBool(self):
        return self.unpack('?')

    def readInt16(self):
        return self.unpack('h', 2)

    def readUInt16(self):
        return self.unpack('H', 2)

    def readInt32(self):
        return self.unpack('i', 4)

    def readUInt32(self):
        return self.unpack('I', 4)

    def readString(self):
        length = self.readUChar()
        return self.unpack(str(length) + 's', length)

    def writeBytes(self, value):
        self.base_stream.write(value)

    def writeChar(self, value):
        self.pack('c', value)

    def writeUChar(self, value):
        self.pack('C', value)

    def writeBool(self, value):
        self.pack('?', value)

    def writeInt16(self, value):
        self.pack('h', value)

    def writeUInt16(self, value):
        self.pack('H', value)

    def writeInt32(self, value):
        self.pack('i', value)

    def writeUInt32(self, value):
        self.pack('I', value)

    def writeString(self, value):
        length = len(value)
        self.writeUChar(length)
        self.pack(str(length) + 's', value)

    def pack(self, fmt, data):
        return self.writeBytes(pack(fmt, data))

    def unpack(self, fmt, length = 1):
        return unpack(fmt, self.readBytes(length))[0]



def readBits(count, read):
	arr = []
	b = 0
	bit = 128
	for x in range(count):
		if (bit == 128):
			b = read()
			bit = 1
		else: bit <<= 1
		arr.append((b & bit) == bit)
	return arr

def readWithBits(bits, read):
	arr = []
	for i in range(len(bits)):
		if bits[i]: arr.append(read())
		else: arr.append(1)
	return arr

if __name__ == '__main__':
	with open('/home/andrew/My Games/Terraria/Players/TimePath.bak/1162047362.map', 'rb') as fd:
		stream = BinaryStream(fd)
		curRelease = stream.readInt32()
		
		print('Release: {0}'.format(curRelease))
		
		worldName = stream.readString()
		worldID = stream.readInt32()
		maxTilesY = stream.readInt32()
		maxTilesX = stream.readInt32()
		
		TileIDCount = stream.readInt16()
		WallIDCount = stream.readInt16()
		maxLiquidTypes = stream.readInt16()
		
		# maxSkyGradients, maxDirtGradients, maxRockGradients
		num7 = stream.readInt16()
		num8 = stream.readInt16()
		num9 = stream.readInt16()
		
		print(worldName)
		print(maxTilesY)
		print(maxTilesX)
		
		array3 = readWithBits(readBits(TileIDCount, stream.readChar), stream.readChar)
		array4 = readWithBits(readBits(WallIDCount, stream.readChar), stream.readChar)
		
		num12 = (int)(sum(array3) + sum(array4) + maxLiquidTypes + num7 + num8 + num9 + 2);
		print('Offset: {0}'.format(stream.base_stream.tell()))
		compressed = stream.readBytes(None)
		print('Offset: {0}'.format(stream.base_stream.tell()))
		print('Compressed size: {0}'.format(len(compressed)))
		bytestr = zlib.decompress(compressed, -zlib.MAX_WBITS) # FIXME: this fails
		stream = BinaryStream(io.BytesIO(bytestr))
		
		for l in range(maxTilesY):
			for m in range(maxTilesX):
				b3 = stream.readChar()
				b4 = 0
				if (b3 & 0b1) == 0b1: b4 = stream.readChar()
				b5 = (b3 & 0b1110) >> 1
				
				flag = {1: True, 2: True, 7: True}.get(b5, False)
				num27 = 0
				if flag:
					if (b3 & 0b1111) == 0b1111:
						num27 = stream.readUInt16()
					else:
						num27 = stream.readChar()
				
				b6 = 255 # light, 255 has special meaning
				if (b3 & 0b100000) == 0b100000: b6 = stream.readChar()
				
				n = {1: stream.readChar, 2: stream.readInt16}.get((b3 & 0b11000000) >> 6, lambda: 0)()
				
				if not b5:
					m += n
					continue
				
				# Other map stuff
				
				for i in range(n):
					m += 1
					if b6 != 255: stream.readChar()
