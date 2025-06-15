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
MODE_OFFSET     = 268   # yst_mode  offset 268 (4 bytes unsigned)
UID_OFFSET      = 272   # yst_uid   offset 272 (4 bytes unsigned)
GID_OFFSET      = 276   # yst_gid   offset 276 (4 bytes unsigned)
ATIME_OFFSET    = 280   # yst_atime offset 280 (4 bytes unsigned)
MTIME_OFFSET    = 284   # yst_mtime offset 284 (4 bytes unsigned)
CTIME_OFFSET    = 288   # yst_ctime offset 288 (4 bytes unsigned)
FILESIZE_OFFSET = 292   # fileSize  offset 292 (4 bytes THIS IS SIGNED)

YAFFS_OBJECT_TYPE_FILE       = 1
YAFFS_OBJECT_TYPE_SYMLINK    = 2
YAFFS_OBJECT_TYPE_DIRECTORY  = 3
YAFFS_OBJECT_TYPE_HARDLINK   = 4
YAFFS_OBJECT_TYPE_SPECIAL    = 5
YAFFS_OBJECT_TYPE_UNKNOWN    = 6

TYPE_NAMES = {
    YAFFS_OBJECT_TYPE_FILE:      "file",
    YAFFS_OBJECT_TYPE_DIRECTORY: "dir",
    YAFFS_OBJECT_TYPE_SYMLINK:   "symlink",
    YAFFS_OBJECT_TYPE_HARDLINK:  "hardlink",
    YAFFS_OBJECT_TYPE_SPECIAL:   "special",
    YAFFS_OBJECT_TYPE_UNKNOWN:   "unknown",
}

def detect_layout(fd):
    max_chunk, max_spare = POSSIBLE_LAYOUTS[-1]
    read_len = 2 * (max_chunk + max_spare)
    buffer = fd.read(read_len)

    if len(buffer) < read_len:
        print("ERROR: Not enugh bytes, can't identify layout.", file=sys.stderr)
        sys.exit(1)

    for chunk_size, spare_size in POSSIBLE_LAYOUTS:
        off1 = chunk_size
        off2 = 2 * chunk_size + spare_size
        if off2 + TAG_STRUCT.size > len(buffer):
            continue
        seq1, objId1, chunkId1, byteCount1 = TAG_STRUCT.unpack_from(buffer, off1)
        seq2, objId2, chunkId2, byteCount2 = TAG_STRUCT.unpack_from(buffer, off2)

        if byteCount1 == 0x0000FFFF and chunkId1 == 0:
            if (byteCount2 == 0x0000FFFF and chunkId2 == 0) or (objId2 == objId1 and chunkId2 == 1):
                fd.seek(0, os.SEEK_SET)
                return chunk_size, spare_size

    print("ERROR: Could not detect layout.",file=sys.stderr)
    sys.exit(1)

# Use basically chunkè_siz + spare_size
# Return EOF, or the data
def read_chunk(fd, chunk_size, spare_size):
    total = chunk_size + spare_size
    data = fd.read(total)
    if not data:
        return None, None
    if len(data) != total:
        print("ERROR: The chuck has been cut for some reason", file=sys.stderr)
        sys.exit(1)
    return data[:chunk_size], data[chunk_size:]

def extract_header_fields(chunk_data):
    """
    If thats a chunck containing an object header, we get:
    - obj_type   (32-bit int)
    - parent_id  (32-bit)
    - name       (null-terminated string) I think ?????
    - mode       (32-bit)
    - uid        (32-bit)
    - gid        (32-bit)
    - atime      (32-bit)
    - mtime      (32-bit)
    - ctime      (32-bit)
    - fileSize   (32-bit)
    """
    obj_type, parent_id = HEADER_TYPE_PARENT_STRUCT.unpack_from(chunk_data, 0)

    # get name
    name_bytes = chunk_data[NAME_OFFSET : NAME_OFFSET + (MAX_NAME_LEN + 1)]
    try:
        # nul = name_bytes.index(b'\xFF')
        nul = name_bytes.index(b'\x00')
        name = name_bytes[:nul].decode('utf-8', errors='replace')
    except ValueError:
        name = name_bytes.decode('utf-8', errors='replace').rstrip('\x00')

    def get_uint(offset):
        return struct.unpack_from("<I", chunk_data, offset)[0]

    def get_int(offset):
        return struct.unpack_from("<i", chunk_data, offset)[0]

    mode     = get_uint(MODE_OFFSET)
    uid      = get_uint(UID_OFFSET)
    gid      = get_uint(GID_OFFSET)
    atime    = get_uint(ATIME_OFFSET)
    mtime    = get_uint(MTIME_OFFSET)
    ctime    = get_uint(CTIME_OFFSET)
    fileSize = get_int(FILESIZE_OFFSET)

    return {
        "type": obj_type,
        "parent_id": parent_id,
        "name": name,
        "mode": mode,
        "uid": uid,
        "gid": gid,
        "atime": atime,
        "mtime": mtime,
        "ctime": ctime,
        "fileSize": fileSize,
    }


def format_metadata(meta):
    # Use dict to build our string:
    # "type + size + mode + uid + gid + atime + mtime + ctime"
    
    tname = TYPE_NAMES.get(meta["type"], str(meta["type"]))
    size_str = f"size={meta['fileSize']}" if meta["type"] == YAFFS_OBJECT_TYPE_FILE else ""

    # Mode in octal (only lower 12 bits: perms + suid/sgid/sticky)
    mode_octal = format(meta["mode"] & 0o7777, "04o")

    uid_str = f"uid={meta['uid']}"
    gid_str = f"gid={meta['gid']}"

    # Timestamps to ISO format
    def iso(ts):
        try:
            return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ts))
        except (ValueError, OSError):
            return str(ts)

    atime_str = f"atime={iso(meta['atime'])}"
    mtime_str = f"mtime={iso(meta['mtime'])}"
    ctime_str = f"ctime={iso(meta['ctime'])}"

    parts = [f"type={tname}"]
    if size_str:
        parts.append(size_str)
    parts.extend([f"mode={mode_octal}", uid_str, gid_str, atime_str, mtime_str, ctime_str])
    # parts.extend([f"mode={mode_octal}", atime_str, mtime_str, ctime_str])

    return "[" + " ".join(parts) + "]"


def build_tree(paths, dir_set):
    
    # Build a nested dict:
    
    tree = {}
    for p in sorted(paths):
        parts = p.split('/')
        node = tree
        for i, part in enumerate(parts):
            is_last = (i == len(parts) - 1)
            if is_last:
                if p in dir_set:
                    node.setdefault(part, {})
                else:
                    node.setdefault(part, None)
            else:
                node = node.setdefault(part, {})
    return tree


def print_tree(node, prefix="", parent_path="", metadata_map=None):
    # Just some fancy presentation of the nested tree in terminal
    entries = sorted(node.items(), key=lambda kv: kv[0].lower())
    for idx, (name, child) in enumerate(entries):
        is_last = (idx == len(entries) - 1)
        branch = "└── " if is_last else "├── "

        if parent_path == "":
            full_path = name
        else:
            full_path = f"{parent_path}/{name}"

        meta_str = ""
        if metadata_map and full_path in metadata_map:
            meta_str = " " + format_metadata(metadata_map[full_path])

        if child is None:       # File
            print(f"{prefix}{branch}{name}{meta_str}")
        else:       # Directory
            print(f"{prefix}{branch}{name}/{meta_str}")
            extension = "    " if is_last else "│   "
            print_tree(child, prefix + extension, full_path, metadata_map)


def list_yaffs2_tree_metadata(image_path):

    objects = {1: "."}      # Basically our root
    dir_set = set(["."])
    all_paths = []
    metadata_map = {}

    try:
        fd = open(image_path, "rb")
    except FileNotFoundError:
        print(f"ERROR: '{image_path}' not found.", file=sys.stderr)
        sys.exit(1)
    
    chunk_size, spare_size = detect_layout(fd)

    # Read all chunks
    while True:
        chunk_data, spare_data = read_chunk(fd, chunk_size, spare_size)
        if chunk_data is None:  # EOF
            break

        seq, object_id, chunk_id, byte_count = TAG_STRUCT.unpack_from(spare_data, 0)

        # Skip erased chunks
        if byte_count == 0xFFFFFFFF:
            continue

        if byte_count != 0x0000FFFF:
            continue

        # Extract all header fields
        meta = extract_header_fields(chunk_data)
        obj_type = meta["type"]
        parent_id = meta["parent_id"]
        name = meta["name"]

        # Build full path
        if parent_id == 1:
            full_path = name
        else:
            parent_path = objects.get(parent_id, "")
            if parent_path in ("", "."):
                full_path = name
            else:
                full_path = f"{parent_path}/{name}"

        # Path + metadata
        objects[object_id] = full_path
        all_paths.append(full_path)
        metadata_map[full_path] = meta
        if obj_type == YAFFS_OBJECT_TYPE_DIRECTORY:
            dir_set.add(full_path)

        # Regular file => skip data
        if obj_type == YAFFS_OBJECT_TYPE_FILE:
            file_size = meta["fileSize"]
            remain = file_size
            while remain > 0:
                next_chunk_data, next_spare_data = read_chunk(fd, chunk_size, spare_size)
                if next_chunk_data is None:
                    print("ERROR: unexpected EOF ????", file=sys.stderr)
                    sys.exit(1)
                _, _, _, next_byte_count = TAG_STRUCT.unpack_from(next_spare_data, 0)
                if next_byte_count == 0xFFFFFFFF:
                    continue
                remain -= next_byte_count

    fd.close()

    # Tree
    tree = build_tree(all_paths, dir_set)

    # Print tree
    print(".root/")
    print_tree(tree, prefix="", parent_path="", metadata_map=metadata_map)


if __name__ == "__main__":
    list_yaffs2_tree_metadata("yaffs2_image.img")