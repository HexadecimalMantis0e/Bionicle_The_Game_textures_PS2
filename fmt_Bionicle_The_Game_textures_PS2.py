from inc_noesis import *
import noesis
import rapi
import struct
import io

def registerNoesisTypes():
    handle = noesis.register("Bionicle: The Game textures", ".bin")
    noesis.setHandlerTypeCheck(handle, btgCheckType)
    noesis.setHandlerLoadRGBA(handle, btgLoadRGBA)
    noesis.logPopup()
    return 1

def btgCheckType(data):
    return 1

def handlePalette(texturePalette, texturePaletteOff, textureType):
    f0 = io.BytesIO(texturePalette)
    f1 = io.BytesIO(texturePalette)
    count = 0
    swapCount = 0

    while count != 0x100:
        color = struct.unpack("<I", f0.read(4))[0]
        f1.write(struct.pack("<I", color))
        count += 1
        swapCount += 1

        if count == 8 or swapCount == 16:
            block0 = f0.read(0x20)
            block1 = f0.read(0x20)
            f1.write(block1)
            f1.write(block0)
            count += 16
            swapCount = 0

    f1.seek(0x00, io.SEEK_SET)

    if textureType == 0x14:
        f1.seek(texturePaletteOff * 0x40, io.SEEK_SET)
        palette = f1.read(0x40)
    else:
        palette = f1.read()
    return bytearray(palette)

def handleTexture(bitStream, texturePalette, textureType, textureWidth, textureHeight):
    if textureType == 0x13:   # 8-bit
        texture = rapi.imageDecodeRawPal(bitStream.readBytes(textureWidth * textureHeight), texturePalette, textureWidth, textureHeight, 8, "r8g8b8a8")
    elif textureType == 0x14: # 4-bit
        texture = rapi.imageDecodeRawPal(bitStream.readBytes((textureWidth * textureHeight) // 0x02), texturePalette, textureWidth, textureHeight, 4, "r8g8b8a8")
    elif textureType == 0x00: # Raw
        texture = rapi.imageDecodeRaw(bitStream.readBytes(textureWidth * textureHeight * 0x04), textureWidth, textureHeight, "r8g8b8a8")
    return texture

def btgLoadRGBA(data, texList):
    texHeaders = [
        0x004F92D0, # 0x74
        0x004F9260, # 0x73
        0x004F8288, # 0x73
        0x004F8298, # 0x73
        0x004F8280, # 0x73
        0x004F61C8, # 0x70
        0x004F7218, # 0x70
        0x004F5110, # 0x6F
        0x004F5130, # 0x6E
        0x004FF504, # 0x6C
        0x004FD320, # 0x6C
        0x00543B28  # 0x65
    ]

    texPackageHeaders = [
        0x004F92E4, # 0x74
        0x004F9274, # 0x73
        0x004F829C, # 0x73
        0x004F61DC, # 0x70
        0x004F722C, # 0x70
        0x004F5124, # 0x6F
        0x004FF518  # 0x6C
    ]

    texCount = 0
    bs = NoeBitStream(data)
    fileSizeDiv4 = bs.getSize() // 4

    for i in range(0, fileSizeDiv4 - 1):
        temp = bs.readUInt()

        if temp in texHeaders:
            address = bs.tell()
            texCheck1 = bs.readUInt()
            texCheck2 = bs.readUInt()

            if (texCheck1 == texCheck2 == 0x00):
                texCount += 1
                bs.seek(0x01, NOESEEK_REL)
                palOffset = bs.readUByte()
                type = bs.readUByte()

                if (temp == 0x00543B28):
                    bs.seek(0x05, NOESEEK_REL)
                    palAddress = bs.readUInt()
                    bs.seek(0x18, NOESEEK_REL)
                else:
                    bs.seek(0x19, NOESEEK_REL)
                    palAddress = bs.readUInt()
                    bs.seek(0x0C, NOESEEK_REL)

                width = bs.readUInt()
                height = bs.readUInt()
                texAddress = bs.readUInt()
                print(texCount)
                print("Found a texture at " + str(hex(address - 0x04)) + ", width - " + str(width) + ", height - " + str(height))

                if type != 0x00:
                    bs.seek(palAddress, NOESEEK_ABS)
                    print("Found a palette at " + str(hex(palAddress)))
                    bs.seek(0x50, NOESEEK_REL)
                    pal = handlePalette(bs.readBytes(0x400), palOffset, type)
                else:
                    pal = None

                bs.seek(texAddress + 0x20, NOESEEK_ABS)
                img = handleTexture(bs, pal, type, width, height)
                texList.append(NoeTexture(str(texCount), width, height, img, noesis.NOESISTEX_RGBA32))

            bs.seek(address, NOESEEK_ABS)

        elif temp in texPackageHeaders:
            address = bs.tell()
            texCheck1 = bs.readUInt()
            texCheck2 = bs.readUInt()

            if (texCheck1 == texCheck2 == 0x00):
                bs.seek(0x01, NOESEEK_REL)
                palOffset = bs.readUByte()
                type = bs.readUByte()
                bs.seek(0x05, NOESEEK_REL)
                palAddress = bs.readUInt()
                bs.seek(0x20, NOESEEK_REL)
                numOfTex = bs.readShort()
                print("Found a texture package at " + str(hex(address - 0x04)) + ", number of textures - " + str(numOfTex))
                bs.seek(0x02, NOESEEK_REL)
                infoAddress = bs.readUInt()
                bs.seek(infoAddress, NOESEEK_ABS)

                for j in range(0, numOfTex):
                    texCount += 1
                    bs.seek(0x08, NOESEEK_REL)
                    width = bs.readUInt()
                    height = bs.readUInt()
                    texAddress = bs.readUInt()
                    print(texCount)
                    print("Found a texture at " + str(hex(address - 0x04)) + ", width - " + str(width) + ", height - " + str(height))

                    if type != 0x00:
                        bs.seek(palAddress, NOESEEK_ABS)
                        print("Found a palette at " + str(hex(palAddress)))
                        bs.seek(0x50, NOESEEK_REL)
                        pal = handlePalette(bs.readBytes(0x400), palOffset, type)
                    else:
                        pal = None

                    bs.seek(texAddress + 0x20, NOESEEK_ABS)
                    img = handleTexture(bs, pal, type, width, height)
                    texList.append(NoeTexture(str(texCount), width, height, img, noesis.NOESISTEX_RGBA32))
                    bs.seek(infoAddress + ((j + 1) * 0x18), NOESEEK_ABS)

            bs.seek(address, NOESEEK_ABS)
    return 1
