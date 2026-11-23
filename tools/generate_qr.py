#!/usr/bin/env python3
"""Generate a dependency-free Clancy-themed QR card and high-resolution PNG."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = "https://jorgealbertt.github.io/clancy-cumpleanos/"
VERSION = 4
SIZE = VERSION * 4 + 17
ECC_CODEWORDS_PER_BLOCK = 18
BLOCK_COUNT = 2
MODULES_PER_INCH = 40
BACKGROUND = (255, 250, 240)
FOREGROUND = (32, 25, 23)


def gf_multiply(left: int, right: int) -> int:
    product = 0
    for _ in range(8):
        if right & 1:
            product ^= left
        right >>= 1
        left <<= 1
        if left & 0x100:
            left ^= 0x11D
    return product


def reed_solomon_generator(degree: int) -> list[int]:
    result = [1]
    root = 1
    for _ in range(degree):
        expanded = [0] * (len(result) + 1)
        for index, coefficient in enumerate(result):
            expanded[index] ^= coefficient
            expanded[index + 1] ^= gf_multiply(coefficient, root)
        result = expanded
        root = gf_multiply(root, 2)
    return result


def reed_solomon_remainder(data: list[int], degree: int) -> list[int]:
    generator = reed_solomon_generator(degree)
    remainder = [0] * degree
    for value in data:
        factor = value ^ remainder.pop(0)
        remainder.append(0)
        for index in range(degree):
            remainder[index] ^= gf_multiply(generator[index + 1], factor)
    return remainder


def encoded_codewords(payload: bytes) -> list[int]:
    bits: list[int] = []

    def append_bits(value: int, length: int) -> None:
        bits.extend((value >> shift) & 1 for shift in range(length - 1, -1, -1))

    append_bits(0b0100, 4)
    append_bits(len(payload), 8)
    for byte in payload:
        append_bits(byte, 8)

    data_capacity = 64 * 8
    bits.extend([0] * min(4, data_capacity - len(bits)))
    bits.extend([0] * ((-len(bits)) % 8))
    data = [sum(bits[start + offset] << (7 - offset) for offset in range(8))
            for start in range(0, len(bits), 8)]
    padding = (0xEC, 0x11)
    while len(data) < 64:
        data.append(padding[(len(data) - ((len(bits) + 7) // 8)) % 2])

    blocks = [data[index * 32:(index + 1) * 32] for index in range(BLOCK_COUNT)]
    checks = [reed_solomon_remainder(block, ECC_CODEWORDS_PER_BLOCK) for block in blocks]
    return (
        [block[index] for index in range(32) for block in blocks]
        + [check[index] for index in range(ECC_CODEWORDS_PER_BLOCK) for check in checks]
    )


def blank_matrix() -> tuple[list[list[bool]], list[list[bool]]]:
    matrix = [[False] * SIZE for _ in range(SIZE)]
    reserved = [[False] * SIZE for _ in range(SIZE)]

    def set_function(x: int, y: int, dark: bool) -> None:
        if 0 <= x < SIZE and 0 <= y < SIZE:
            matrix[y][x] = dark
            reserved[y][x] = True

    for center_x, center_y in ((3, 3), (SIZE - 4, 3), (3, SIZE - 4)):
        for dy in range(-1, 8):
            for dx in range(-1, 8):
                distance = max(abs(dx - 3), abs(dy - 3))
                set_function(center_x + dx - 3, center_y + dy - 3, distance not in (2, 4))

    for index in range(8, SIZE - 8):
        set_function(index, 6, index % 2 == 0)
        set_function(6, index, index % 2 == 0)

    for dy in range(-2, 3):
        for dx in range(-2, 3):
            set_function(SIZE - 7 + dx, SIZE - 7 + dy, max(abs(dx), abs(dy)) != 1)

    format_positions = [
        [(8, index) for index in range(6)]
        + [(8, 7), (8, 8), (7, 8)]
        + [(14 - index, 8) for index in range(9, 15)],
        [(SIZE - 1 - index, 8) for index in range(8)]
        + [(8, SIZE - 15 + index) for index in range(8, 15)],
    ]
    for positions in format_positions:
        for x, y in positions:
            reserved[y][x] = True
    set_function(8, SIZE - 8, True)
    return matrix, reserved


def mask_applies(mask: int, x: int, y: int) -> bool:
    conditions = (
        (x + y) % 2 == 0,
        y % 2 == 0,
        x % 3 == 0,
        (x + y) % 3 == 0,
        (y // 2 + x // 3) % 2 == 0,
        (x * y) % 2 + (x * y) % 3 == 0,
        ((x * y) % 2 + (x * y) % 3) % 2 == 0,
        ((x + y) % 2 + (x * y) % 3) % 2 == 0,
    )
    return conditions[mask]


def format_bits(mask: int) -> int:
    value = mask  # Error-correction level M is encoded as 00.
    remainder = value
    for _ in range(10):
        remainder = (remainder << 1) ^ ((remainder >> 9) * 0x537)
    return ((value << 10) | remainder) ^ 0x5412


def draw_format(matrix: list[list[bool]], mask: int) -> None:
    data = format_bits(mask)
    positions = [
        [(8, index) for index in range(6)]
        + [(8, 7), (8, 8), (7, 8)]
        + [(14 - index, 8) for index in range(9, 15)],
        [(SIZE - 1 - index, 8) for index in range(8)]
        + [(8, SIZE - 15 + index) for index in range(8, 15)],
    ]
    for copy in positions:
        for index, (x, y) in enumerate(copy):
            matrix[y][x] = bool((data >> index) & 1)
    matrix[SIZE - 8][8] = True


def place_data(
    base: list[list[bool]],
    reserved: list[list[bool]],
    codewords: list[int],
    mask: int,
) -> list[list[bool]]:
    matrix = [row[:] for row in base]
    bits = [(byte >> shift) & 1 for byte in codewords for shift in range(7, -1, -1)]
    bit_index = 0
    upward = True
    right = SIZE - 1
    while right >= 1:
        if right == 6:
            right = 5
        for offset in range(SIZE):
            y = SIZE - 1 - offset if upward else offset
            for x in (right, right - 1):
                if not reserved[y][x]:
                    bit = bits[bit_index] if bit_index < len(bits) else 0
                    matrix[y][x] = bool(bit ^ mask_applies(mask, x, y))
                    bit_index += 1
        upward = not upward
        right -= 2
    if bit_index < len(bits):
        raise ValueError("The QR version does not have enough data modules.")
    draw_format(matrix, mask)
    return matrix


def penalty(matrix: list[list[bool]]) -> int:
    score = 0

    def score_line(line: list[bool]) -> int:
        line_score = 0
        run_color = line[0]
        run_length = 1
        for cell in line[1:]:
            if cell == run_color:
                run_length += 1
            else:
                if run_length >= 5:
                    line_score += 3 + run_length - 5
                run_color = cell
                run_length = 1
        if run_length >= 5:
            line_score += 3 + run_length - 5
        for start in range(len(line) - 10):
            pattern = line[start:start + 11]
            if pattern in ([True, False, True, True, True, False, True, False, False, False, False],
                           [False, False, False, False, True, False, True, True, True, False, True]):
                line_score += 40
        return line_score

    for row in matrix:
        score += score_line(row)
    for x in range(SIZE):
        score += score_line([matrix[y][x] for y in range(SIZE)])

    for y in range(SIZE - 1):
        for x in range(SIZE - 1):
            color = matrix[y][x]
            if matrix[y][x + 1] == color and matrix[y + 1][x] == color and matrix[y + 1][x + 1] == color:
                score += 3

    dark_count = sum(sum(row) for row in matrix)
    score += int(abs(dark_count * 100 / (SIZE * SIZE) - 50) // 5) * 10
    return score


def make_matrix(payload: bytes) -> tuple[list[list[bool]], int, list[list[bool]]]:
    codewords = encoded_codewords(payload)
    base, reserved = blank_matrix()
    candidates = [(penalty(matrix := place_data(base, reserved, codewords, mask)), mask, matrix)
                  for mask in range(8)]
    _, mask, matrix = min(candidates, key=lambda candidate: candidate[0])
    return matrix, mask, reserved


def svg_document(matrix: list[list[bool]]) -> str:
    module = 12
    quiet = 4
    card_x, card_y = 28, 28
    qr_x, qr_y = 44, 142
    qr_size = (SIZE + quiet * 2) * module
    commands = []
    for y, row in enumerate(matrix):
        for x, dark in enumerate(row):
            if dark:
                px = qr_x + (x + quiet) * module
                py = qr_y + (y + quiet) * module
                commands.append(f"M{px} {py}h{module}v{module}h-{module}z")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="580" height="720" viewBox="0 0 580 720" role="img" aria-labelledby="title description">
  <title id="title">QR Clancy — edición de cumpleaños</title>
  <desc id="description">Código QR de alto contraste para abrir {DESTINATION}</desc>
  <rect width="580" height="720" fill="#171312"/>
  <rect x="{card_x}" y="{card_y}" width="524" height="680" rx="22" fill="#f7f1e7"/>
  <path d="M50 52h480" stroke="#702d29" stroke-width="5"/>
  <circle cx="66" cy="82" r="13" fill="#702d29"/>
  <text x="91" y="89" fill="#211918" font-family="Georgia,serif" font-size="29" font-weight="700" letter-spacing="3">CLANCY</text>
  <text x="91" y="113" fill="#702d29" font-family="monospace" font-size="11" letter-spacing="2">EDICIÓN DE CUMPLEAÑOS · 24—11</text>
  <rect x="{qr_x}" y="{qr_y}" width="{qr_size}" height="{qr_size}" fill="#fffaf0"/>
  <path d="{' '.join(commands)}" fill="#201917" shape-rendering="crispEdges"/>
  <path d="M50 650h480" stroke="#d8c8ae" stroke-width="1"/>
  <text x="290" y="676" fill="#702d29" font-family="monospace" font-size="11" letter-spacing="1.2" text-anchor="middle">ESCANEA PARA ABRIR EL RECUERDO</text>
  <text x="290" y="699" fill="#211918" font-family="monospace" font-size="10" text-anchor="middle">jorgealbertt.github.io/clancy-cumpleanos</text>
</svg>
"""


def png_chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)


def write_png(path: Path, matrix: list[list[bool]]) -> None:
    quiet = 4
    scale = MODULES_PER_INCH
    modules = SIZE + quiet * 2
    dimension = modules * scale
    scanline = bytearray([0] + list(BACKGROUND) * dimension)
    pixels = bytearray(scanline * dimension)

    for y, row in enumerate(matrix):
        for x, dark in enumerate(row):
            if not dark:
                continue
            left = (x + quiet) * scale
            top = (y + quiet) * scale
            for py in range(top, top + scale):
                start = py * len(scanline) + 1 + left * 3
                pixels[start:start + scale * 3] = bytes(FOREGROUND) * scale

    header = struct.pack(">IIBBBBB", dimension, dimension, 8, 2, 0, 0, 0)
    compressed = zlib.compress(bytes(pixels), level=9)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", header)
                     + png_chunk(b"IDAT", compressed) + png_chunk(b"IEND", b""))


def verify_matrix(matrix: list[list[bool]], mask: int, reserved: list[list[bool]], payload: bytes) -> None:
    bits = []
    upward = True
    right = SIZE - 1
    while right >= 1:
        if right == 6:
            right = 5
        for offset in range(SIZE):
            y = SIZE - 1 - offset if upward else offset
            for x in (right, right - 1):
                if not reserved[y][x]:
                    bits.append(int(matrix[y][x]) ^ int(mask_applies(mask, x, y)))
        upward = not upward
        right -= 2

    codewords = [sum(bits[start + offset] << (7 - offset) for offset in range(8))
                 for start in range(0, 800, 8)]
    blocks = [
        [codewords[index] for index in range(block, 64, 2)]
        + [codewords[index] for index in range(64 + block, 100, 2)]
        for block in range(2)
    ]
    if any(reed_solomon_remainder(block[:32], ECC_CODEWORDS_PER_BLOCK) != block[32:] for block in blocks):
        raise ValueError("QR Reed–Solomon verification failed.")

    data = [codewords[index] for index in range(0, 64, 2)]
    data.extend(codewords[index] for index in range(1, 64, 2))
    stream = [bit for byte in data for bit in (byte >> shift & 1 for shift in range(7, -1, -1))]
    read_index = 0

    def read_bits(count: int) -> int:
        nonlocal read_index
        value = 0
        for _ in range(count):
            value = (value << 1) | stream[read_index]
            read_index += 1
        return value

    if read_bits(4) != 0b0100:
        raise ValueError("QR byte-mode verification failed.")
    decoded = bytes(read_bits(8) for _ in range(read_bits(8)))
    if decoded != payload:
        raise ValueError("Decoded QR contents do not match the published URL.")


def verify_png(path: Path, matrix: list[list[bool]]) -> None:
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Generated PNG has an invalid signature.")
    offset = 8
    image_data = bytearray()
    while offset < len(raw):
        length = struct.unpack_from(">I", raw, offset)[0]
        kind = raw[offset + 4:offset + 8]
        data = raw[offset + 8:offset + 8 + length]
        crc = struct.unpack_from(">I", raw, offset + 8 + length)[0]
        if zlib.crc32(kind + data) & 0xFFFFFFFF != crc:
            raise ValueError("Generated PNG has a corrupt chunk.")
        if kind == b"IHDR":
            width, height, depth, color_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", data)
            if (width, height, depth, color_type, compression, filtering, interlace) != (
                (SIZE + 8) * MODULES_PER_INCH, (SIZE + 8) * MODULES_PER_INCH, 8, 2, 0, 0, 0
            ):
                raise ValueError("Generated PNG has unexpected dimensions or pixel format.")
        elif kind == b"IDAT":
            image_data.extend(data)
        elif kind == b"IEND":
            break
        offset += length + 12

    pixels = zlib.decompress(image_data)
    stride = 1 + width * 3
    if len(pixels) != stride * height or any(pixels[y * stride] != 0 for y in range(height)):
        raise ValueError("Generated PNG scanlines could not be verified.")
    quiet = 4
    for y, row in enumerate(matrix):
        for x, dark in enumerate(row):
            px = (x + quiet) * MODULES_PER_INCH + MODULES_PER_INCH // 2
            py = (y + quiet) * MODULES_PER_INCH + MODULES_PER_INCH // 2
            expected = FOREGROUND if dark else BACKGROUND
            start = py * stride + 1 + px * 3
            if tuple(pixels[start:start + 3]) != expected:
                raise ValueError("Rendered PNG does not match the verified QR matrix.")


def main() -> None:
    payload = DESTINATION.encode("utf-8")
    matrix, mask, reserved = make_matrix(payload)
    verify_matrix(matrix, mask, reserved, payload)

    qr_dir = ROOT / "qr"
    qr_dir.mkdir(exist_ok=True)
    (qr_dir / "clancy-cumpleanos.svg").write_text(svg_document(matrix), encoding="utf-8")
    png_path = qr_dir / "clancy-cumpleanos.png"
    write_png(png_path, matrix)
    verify_png(png_path, matrix)
    print(f"Generated and verified {qr_dir / 'clancy-cumpleanos.svg'}")
    print(f"Generated and verified {png_path} ({(SIZE + 8) * MODULES_PER_INCH} x {(SIZE + 8) * MODULES_PER_INCH})")


if __name__ == "__main__":
    main()
