import struct
import os
import argparse
import sys

def getVersion(file_path):
    with open(file_path, "rb") as f:
        # Check signature? Usually first 8 bytes
        # For RGSS3A it starts with 'RGSSAD\0\3'
        data = f.read(8)
        print("Header:", data)
        return data

def decryptNameV3(value, key):
    name_dec = bytearray(len(value))
    bkey = key.to_bytes(4, 'little')

    j = 0
    for i in range(0, len(value)):
        if(j == 4):
            j = 0
        name_dec[i] = value[i] ^ bkey[j]
        j += 1
    # Filenames might be utf-8 or other encoding. Using 'utf-8' with replacement for safety.
    return name_dec.decode('utf-8', errors='replace')


def decryptFile(archive_path, file_offset, file_size, file_name, file_key):
    # file_key is the starting key for the file data
    # key (global metadata key) is NOT used for file data content in RGSS3A, only file_key.

    with open(archive_path, "rb") as f:
        f.seek(file_offset)
        # Read in chunks to handle large files better, but for now read all (as per original logic but improved)
        # To avoid memory issues with huge files, chunking would be better.
        # But sticking to "finishing the prototype", let's fix logic first.
        data = f.read(file_size)
        dec_file = bytearray(len(data))

        iTempKey = file_key
        bTempKey = iTempKey.to_bytes(4, 'little')

        j = 0
        for i in range(0, len(data)):
            if j == 4:
                j = 0
                iTempKey = (iTempKey * 7 + 3) & 0xFFFFFFFF
                bTempKey = iTempKey.to_bytes(4, 'little')

            dec_file[i] = data[i] ^ bTempKey[j]
            j += 1

        print(f"Extracting: {file_name}")
        output_dir = os.path.dirname(file_name)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        with open(file_name, 'wb') as out_f:
            out_f.write(dec_file)


def readRGSSADV3(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    try:
        with open(file_path, 'rb') as fileobj:
            header = fileobj.read(8)
            if header[0:6] != b'RGSSAD':
                print("Invalid RGSSAD header")
                return
            if header[7] != 3:
                print("Only RGSS3A (version 3) is supported by this script.")
                return

            key = struct.unpack('<I', fileobj.read(4))[0]
            key = (key * 9 + 3) & 0xFFFFFFFF

            while True:
                # Read file_offset
                offset_bytes = fileobj.read(4)
                if len(offset_bytes) < 4:
                    break # EOF

                file_offset = decryptIntV3(struct.unpack('<I', offset_bytes)[0], key)

                if(file_offset == 0):
                    break

                file_size = decryptIntV3(struct.unpack('<I', fileobj.read(4))[0], key)
                file_key = decryptIntV3(struct.unpack('<I', fileobj.read(4))[0], key)
                length = decryptIntV3(struct.unpack('<I', fileobj.read(4))[0], key)

                name_bytes = fileobj.read(length)
                file_name = decryptNameV3(name_bytes, key)

                # print(f"[i] Found File: {file_name} Offset: {file_offset} Size: {file_size}")
                decryptFile(file_path, file_offset, file_size, file_name, file_key)
                # print(f"[i] File {file_name} extracted.")

    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()


def decryptIntV3(value, key):
    return int(value ^ key)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RGSS3A Decrypter")
    parser.add_argument("file", help="Path to the .rgss3a file", nargs='?', default="Game.rgss3a")
    args = parser.parse_args()

    print(f"Processing {args.file}...")
    readRGSSADV3(args.file)
