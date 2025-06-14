import struct
import sys
import os
import time

TAG_STRUCT = struct.Struct("<LLLL")
HEADER_TYPE_PARENT_STRUCT = struct.Struct("<II")

POSSIBLE_LAYOUTS = [
    (2048, 64),
    (4096, 128),
    (8192, 256),
    (16384, 512),
]

NAME_OFFSET = 10
MAX_NAME_LEN = 255

# Metadata field offsets in chunk_data
MODE_OFFSET     = 268
UID_OFFSET      = 272
GID_OFFSET      = 276
ATIME_OFFSET    = 280
MTIME_OFFSET    = 284
CTIME_OFFSET    = 288
FILESIZE_OFFSET = 292

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
        seq2, objId2, chunkId2, byteCount2 = TAG_STRUCT.unpack_from(buffer, off2)

        if byteCount1 == 0x0000FFFF and chunkId1 == 0:
            if (byteCount2 == 0x0000FFFF and chunkId2 == 0) or (objId2 == objId1 and chunkId2 == 1):
                fd.seek(0)
                return chunk_size, spare_size

    print("ERROR: Could not detect layout.")
    sys.exit(1)

def read_chunk(fd, chunk_size, spare_size):
    total = chunk_size + spare_size
    data = fd.read(total)
    if not data or len(data) != total:
        return None, None
    return data[:chunk_size], data[chunk_size:]

def extract_name(chunk_data):
    name_bytes = chunk_data[NAME_OFFSET : NAME_OFFSET + MAX_NAME_LEN + 1]
    try:
        nul = name_bytes.index(b'\x00')
        return name_bytes[:nul].decode('utf-8', errors='replace')
    except ValueError:
        return name_bytes.decode('utf-8', errors='replace').rstrip('\x00')

def get_uint32(chunk_data, offset):
    return struct.unpack_from("<I", chunk_data, offset)[0]

def get_int32(chunk_data, offset):
    return struct.unpack_from("<i", chunk_data, offset)[0]

def format_time(ts):
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
    except (OSError, ValueError):
        return str(ts)

def main(image_path):
    with open(image_path, "rb") as fd:
        chunk_size, spare_size = detect_layout(fd)

        while True:
            chunk_data, spare_data = read_chunk(fd, chunk_size, spare_size)
            if chunk_data is None:
                break

            seq, objId, chunkId, byteCount = TAG_STRUCT.unpack_from(spare_data, 0)
            if byteCount != 0x0000FFFF:
                continue

            obj_type, parentId = HEADER_TYPE_PARENT_STRUCT.unpack_from(chunk_data, 0)
            name = extract_name(chunk_data)

            mode     = get_uint32(chunk_data, MODE_OFFSET)
            uid      = get_uint32(chunk_data, UID_OFFSET)
            gid      = get_uint32(chunk_data, GID_OFFSET)
            fileSize = get_int32(chunk_data, FILESIZE_OFFSET)

            print(f"{objId}: {name}")
            print(f"  Type: {obj_type}, Parent: {parentId}")
            print(f"  Size: {fileSize}, Mode: {oct(mode & 0o7777)}")
            print(f"  UID: {uid}, GID: {gid}")
            print()

if __name__ == "__main__":
    main("yaffs2_image.img")