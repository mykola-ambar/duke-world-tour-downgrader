#!/usr/bin/env python3

import argparse
import os
import sys
import pickle

from binascii import crc32 as signed_crc32
from io import BytesIO
from itertools import accumulate

PATCH_FILENAME = "downgrade_patch.dat"

WORLD_TOUR_CRC32 = 0x982afe4a
ATOMIC_EDITION_CRC32 = 0xfd3dcff1
PATCH_CRC32 = 0xc893abab

HEADER_LENGTH = 16
DIR_ENTRY_LENGTH = 16
LUMP_NAME_LENGTH = 12

LUMP_ORDER = [
    3, 0, 1, 4, 2, 5, 6, 7, 8, 9, 10, 31, 32, 33, 81, 82, 34, 35, 36, 243, 392, 155, 
    381, 384, 368, 251, 367, 366, 189, 369, 314, 358, 383, 385, 357, 356, 355, 359, 
    338, 337, 333, 334, 336, 335, 172, 171, 170, 169, 302, 377, 183, 363, 192, 191,
    186, 396, 388, 164, 352, 451, 398, 316, 317, 399, 437, 257, 256, 395, 416, 137,
    375, 420, 252, 247, 248, 362, 304, 221, 238, 274, 342, 343, 344, 348, 446, 306, 
    229, 345, 347, 349, 346, 205, 206, 193, 439, 202, 134, 207, 312, 376, 380, 387, 
    133, 267, 351, 139, 154, 220, 277, 278, 286, 340, 354, 378, 129, 431, 440, 328, 
    330, 393, 230, 255, 261, 264, 449, 166, 211, 223, 315, 361, 254, 391, 299, 297, 
    298, 260, 432, 417, 429, 249, 250, 426, 242, 371, 323, 364, 339, 181, 318, 450, 
    419, 152, 441, 442, 443, 444, 200, 404, 341, 233, 234, 246, 270, 263, 235, 310, 
    353, 382, 138, 386, 271, 370, 241, 127, 126, 125, 322, 222, 294, 165, 184, 303, 
    397, 212, 273, 224, 225, 226, 227, 228, 379, 332, 188, 311, 272, 157, 232, 240, 
    288, 421, 360, 325, 209, 324, 285, 141, 279, 280, 281, 282, 283, 284, 436, 128, 
    245, 143, 142, 144, 145, 146, 150, 147, 149, 148, 204, 276, 313, 131, 132, 244, 
    300, 372, 430, 168, 201, 414, 413, 409, 410, 412, 411, 198, 197, 194, 196, 195, 
    199, 405, 402, 403, 406, 407, 305, 447, 268, 275, 182, 296, 455, 331, 448, 187, 
    258, 262, 329, 373, 308, 307, 309, 434, 190, 289, 290, 291, 292, 293, 418, 390, 
    151, 400, 326, 327, 236, 216, 217, 218, 219, 215, 208, 213, 214, 422, 423, 424,
    425, 433, 428, 136, 374, 295, 185, 445, 239, 394, 389, 265, 179, 266, 180, 427, 
    162, 159, 160, 161, 163, 158, 156, 177, 176, 175, 178, 174, 173, 130, 301, 135, 
    140, 167, 203, 210, 231, 237, 319, 415, 435, 452, 453, 454, 287, 320, 321, 350, 
    365, 408, 438, 153, 253, 269, 401, 259, 97, 115, 91, 117, 122, 112, 119, 116, 92, 
    98, 106, 95, 94, 100, 101, 118, 84, 83, 85, 86, 96, 99, 104, 107, 111, 113, 114, 
    120, 123, 124, 88, 105, 121, 87, 109, 89, 103, 102, 93, 108, 90, 110, 11, 12, 13, 
    14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 42, 43, 44, 
    45, 46, 48, 51, 52, 53, 54, 55, 56, 57, 58, 49, 50, 59, 62, 63, 64, 65, 66, 67,
    68, 69, 60, 40, 41, 47, 61, 70, 73, 74, 75, 76, 77, 78, 79, 80, 71, 72, 38, 37, 39]

LUMP_DATA_BASE_OFFSET = HEADER_LENGTH + len(LUMP_ORDER) * DIR_ENTRY_LENGTH

def crc32(b) -> int:
    return signed_crc32(b) & 0xFFFFFFFF

def parse_args():
    parser = argparse.ArgumentParser(description="Duke3D World Tour Downgrader")

    parser.add_argument(
        dest="grp_path", type=str, nargs='?', default="DUKE3D.GRP", 
        help="Path to World Tour DUKE3D.GRP file",
    )

    return parser.parse_args()

def main():
    args = parse_args()
    try:
        with open(args.grp_path, 'rb') as grp_file:
            grp_bytes = grp_file.read()
    except OSError as e:
        print(f"Failed to open .GRP file \"{args.grp_path}\": {e}", file=sys.stderr)
        return

    if crc32(grp_bytes) != WORLD_TOUR_CRC32:
        print(f"CRC32 checksum failed for \"{args.grp_path}\"", file=sys.stderr)
        return
    
    try:
        with open(PATCH_FILENAME, 'rb') as patch_file:
            patch_bytes = patch_file.read()
    except OSError as e:
        print(f"Failed to open patch file \"{PATCH_FILENAME}\": {e}", file=sys.stderr)
        return

    if crc32(patch_bytes) != PATCH_CRC32:
        print(f"CRC32 checksum failed for \"{PATCH_FILENAME}\"", file=sys.stderr)
        return

    try:
        patch = pickle.loads(patch_bytes)
    except pickle.PickleError as e:
        print(f"Patch unpickling failed: {e}", file=sys.stderr)
        return

    out_io = BytesIO()

    # Copy the header
    out_io.write(grp_bytes[0:HEADER_LENGTH])

    # Calculate lump data offsets
    lump_data_size_iter = (
        int.from_bytes(
            grp_bytes[
                HEADER_LENGTH + index * DIR_ENTRY_LENGTH + LUMP_NAME_LENGTH
                :HEADER_LENGTH + index * DIR_ENTRY_LENGTH + LUMP_NAME_LENGTH + 4
            ], 'little')
            for index in range(len(LUMP_ORDER)))
    
    lump_offsets = [LUMP_DATA_BASE_OFFSET, *(
            offset + LUMP_DATA_BASE_OFFSET 
            for offset in accumulate(lump_data_size_iter))
    ]

    # The order of lumps differs between DUKE3D.GRP versions.
    # Write reordered lump directory entries
    for lump_index in LUMP_ORDER:
        dir_entry_offset = HEADER_LENGTH + lump_index * DIR_ENTRY_LENGTH
        dir_entry_bytes = bytearray(grp_bytes[dir_entry_offset: dir_entry_offset + DIR_ENTRY_LENGTH])
        # World Tour GRP lump names have stray characters after the first null byte
        # that do not appear in the Atomic Edition GRP
        dir_entry_bytes[:LUMP_NAME_LENGTH] = dir_entry_bytes[:LUMP_NAME_LENGTH].partition(b'\x00')[0].ljust(LUMP_NAME_LENGTH, b'\x00')
        out_io.write(dir_entry_bytes)
    
    assert out_io.tell() == LUMP_DATA_BASE_OFFSET, "incorrect directory size written"
    
    # Write reordered lump data
    for lump_index in LUMP_ORDER:
        lump_data_size = int.from_bytes(
            grp_bytes[
                HEADER_LENGTH + lump_index * DIR_ENTRY_LENGTH + LUMP_NAME_LENGTH
                :HEADER_LENGTH + lump_index * DIR_ENTRY_LENGTH + LUMP_NAME_LENGTH + 4
            ], 'little')
        lump_offset = lump_offsets[lump_index]
        lump_data = bytearray(grp_bytes[lump_offset:lump_offset + lump_data_size])
        try:
            lump_patch = patch[lump_index]
            for offset, xor_bytes in lump_patch:
                for i in range(len(xor_bytes)):
                    lump_data[offset + i] = lump_data[offset + i] ^ xor_bytes[i]
        except KeyError:
            pass
        out_io.write(lump_data)

    out_grp_bytes = out_io.getvalue()

    if crc32(out_grp_bytes) != ATOMIC_EDITION_CRC32:
        print(f"CRC32 checksum failed for downgraded GRP", file=sys.stderr)
        return

    print("Creating backup... ", end="")
    try:
        os.rename(args.grp_path, f"{os.path.basename(args.grp_path)}.bak")
    except OSError as e:
        print(f"Backup failed: {e}", file=sys.stderr)
        return
    else:
        print("done")

    # Write downgraded DUKE3D.grp
    print(f"Writing downgraded \"{args.grp_path}\"... ", end="")
    try:
        with open(args.grp_path, 'wb') as out_grp_file:
            out_grp_file.write(out_grp_bytes)
    except OSError as e:
        print(f"Failed to write \"{args.grp_path}\": {e}", file=sys.stderr)
    else:
        print("done")


if __name__ == "__main__":
    main()
