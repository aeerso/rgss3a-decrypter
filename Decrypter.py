import struct
import os

def getVersion(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        print("RGSSAD Version:", data[7])
        return data[7]

def decryptNameV3(value, key):
    name_dec = bytearray(len(value))
    bkey = key.to_bytes(4, 'little')

    j = 0
    for i in range(0, len(value)):
        if(j == 4):
            j = 0
        name_dec[i] = value[i] ^ bkey[j]
        j += 1
    return name_dec.decode()


def decryptFile(file_offset, file_size, file_name, file_key, key):
    with open("Game.rgss3a", "rb") as f:
        f.seek(file_offset)
        data = f.read(file_size)
        dec_file = bytearray(len(data))
        iTempKey = file_key
        bTempKey = key.to_bytes(4, 'little')
        j = 0
        for i in range(0, len(data)):
            if j == 4:
                j = 0
                iTempKey *= 7
                iTempKey += 3
                #see TODO: we just need the first 4 bytes
                bTempKey = iTempKey.to_bytes(2048, 'little')

            dec_file[i] = data[i] ^ bTempKey[j]
            j += 1
        print(file_name)
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        f = open(file_name, 'w+b')
        f.write(dec_file)
        return


def readRGSSADV3(file_path):

    with open(file_path, 'rb') as fileobj:
        fileobj.seek(8)
        key = struct.unpack('<I', fileobj.read(4))[0]
        key *= 9
        key += 3

        while True:

            file_offset = decryptIntV3(struct.unpack('i', fileobj.read(4))[0], key)

            if(file_offset == 0):
                break
            
            file_size = decryptIntV3(struct.unpack('i', fileobj.read(4))[0], key)
            file_key = decryptIntV3(struct.unpack('i', fileobj.read(4))[0], key)
            lenght = decryptIntV3(struct.unpack('i', fileobj.read(4))[0], key)
            file_name = decryptNameV3(fileobj.read(lenght), key)
            
            print("[i] File:", file_name)
            decryptFile(file_offset,file_size,file_name,file_key,key)
            print("[i] File", file_name, "decrypted.")

            break


def decryptIntV3(value, key):
    return int(value ^ key)

#Edit this idk
getVersion("Game.rgss3a")
readRGSSADV3("Game.rgss3a")
