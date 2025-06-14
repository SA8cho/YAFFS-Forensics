import struct
import sys
import os

# Tag structure
TAG_STRUCT = struct.Struct("<LLLL")
HEADER_TYPE_PARENT_STRUCT = struct.Struct("<II")
NAME_OFFSET = 10  # To check
MAX_NAME_LEN = 255


POSSIBLE_LAYOUTS = [
    (2048, 64),
    (4096, 128)
]

# def dump_hex(buf):  # debug
#     print(' '.join(f'{b:02x}' for b in buf))

def detect_layout(fd):
    max_chunk, max_spare = POSSIBLE_LAYOUTS[-1]
    read_len = 2 * (max_chunk + max_spare)
    buffer = fd.read(read_len)

    for chunk_size, spare_size in POSSIBLE_LAYOUTS:
        off1 = chunk_size
        off2 = 2 * chunk_size + spare_size
        if off2 + TAG_STRUCT.size > len(buffer):
            continue
        seq1, objId1, chunkId1, byteCount1 = TAG_STRUCT.unpack_from(buffer, off1)
        # seq1, objId1, chunkId1, byteCount1 = TAG_STRUCT.unpack_from(buffer, off1 + 1)
        # seq2, objId2, chunkId2, byteCount2 = TAG_STRUCT.unpack_from(buffer, off2 + 1)
        seq2, objId2, chunkId2, byteCount2 = TAG_STRUCT.unpack_from(buffer, off2)

        if byteCount1 == 0x0000FFFF and chunkId1 == 0:      # Not 0x000FFFFF
            if (byteCount2 == 0x0000FFFF and chunkId2 == 0) or (objId2 == objId1 and chunkId2 == 1):
                fd.seek(0)
                return chunk_size, spare_size

    print("ERROR: No layout fund")
    sys.exit(1)

def read_chunk(fd, chunk_size, spare_size):
    total = chunk_size + spare_size
    data = fd.read(total)
    if not data or len(data) != total:
        return None, None
    return data[:chunk_size], data[chunk_size:]

"""
def read_chunk(fd, chunk_size, spare_size):
    total = chunk_size + spare_size
    data = fd.read(total)
    if not data or len(data) != total:
        return None, None
    return data[:chunk_size + spare_size], data[chunk_size: + spare_size]
"""

def extract_name(chunk_data):
    name_bytes = chunk_data[NAME_OFFSET : NAME_OFFSET + MAX_NAME_LEN + 1]
    try:
        nul = name_bytes.index(b'\x00')
        # return name_bytes[:nul].decode('utf-16', errors='replace')
        # print("WARNING: name not endng with nuln")
        return name_bytes[:nul].decode('utf-8', errors='replace')
    except ValueError:
        return name_bytes.decode('utf-8', errors='replace').rstrip('\x00')

def main(image_path):
    with open(image_path, "rb") as fd:
            chunk_size, spare_size = detect_layout(fd)

            while True:
                chunk_data, spare_data = read_chunk(fd, chunk_size, spare_size)
                if chunk_data is None:
                    break

                seq, objId, chunkId, byteCount = TAG_STRUCT.unpack_from(spare_data, 0)
                if byteCount != 0x0000FFFF:
                    print("ERROR: Not supposed to happen ????")

                _, parentId = HEADER_TYPE_PARENT_STRUCT.unpack_from(chunk_data, 0)
                name = extract_name(chunk_data)
                print(f"{objId}: {name}")


if __name__ == "__main__":
    main("yaffs2_image.img")