#!/usr/bin/env python3
"""THE ZERO-G MUG — catalogue photo of an impossible gadget.

Pure Python standard library only: no Pillow, no third-party code of any
kind. The shot is drawn onto an RGB bytearray canvas with small raster
helpers (rectangles, ellipses, lines, a built-in 5x7 bitmap font) and the
PNG is encoded by hand (signature + IHDR + zlib IDAT + IEND). Runs
offline, no network, no randomness, no timestamps — the same bytes
every run. Writes one 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png
(default /output), at most 1 MiB.
"""
import math
import os
import struct
import zlib

W = H = 1024

# ---------------------------------------------------------------- colours
BG_TOP = (238, 238, 236)
BG_BOTTOM = (220, 220, 218)
SHADOW = (198, 198, 196)
SHADOW_DARK = (186, 186, 184)
MUG = (250, 250, 248)
MUG_EDGE = (203, 203, 201)
COFFEE = (101, 67, 50)
COFFEE_DARK = (78, 50, 36)
COFFEE_LIGHT = (150, 110, 80)
CREAM = (235, 220, 200)
GOLD = (212, 164, 74)
GOLD_DARK = (170, 130, 55)
LABEL_INK = (58, 42, 28)
SILVER = (178, 183, 188)
SILVER_DARK = (120, 125, 130)
SILVER_LIGHT = (206, 211, 216)
INK = (44, 44, 46)
GREY = (74, 74, 76)
GREY_SOFT = (110, 110, 113)
RIM = (120, 90, 70)

# ---------------------------------------------------------------- canvas
buf = bytearray(W * H * 3)


def _set(x, y, color):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = color[0]
        buf[i + 1] = color[1]
        buf[i + 2] = color[2]


def fill_rect(x0, y0, x1, y1, color):
    """Fill an axis-aligned rectangle (x1/y1 exclusive)."""
    x0 = max(0, x0)
    y0 = max(0, y0)
    x1 = min(W, x1)
    y1 = min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(color) * (x1 - x0)
    for y in range(y0, y1):
        o = (y * W + x0) * 3
        buf[o:o + len(row)] = row


def fill_ellipse(cx, cy, rx, ry, color):
    """Filled ellipse by scanlines."""
    if rx <= 0 or ry <= 0:
        return
    for y in range(max(0, cy - ry), min(H, cy + ry + 1)):
        dy = (y - cy) / ry
        dx = int(rx * math.sqrt(max(0.0, 1.0 - dy * dy)))
        fill_rect(cx - dx, y, cx + dx + 1, y + 1, color)


def fill_circle(cx, cy, r, color):
    fill_ellipse(cx, cy, r, r, color)


def fill_rounded_rect(x0, y0, x1, y1, r, color):
    fill_rect(x0 + r, y0, x1 - r, y1, color)
    fill_rect(x0, y0 + r, x1, y1 - r, color)
    for (cx, cy) in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                     (x0 + r, y1 - r), (x1 - r, y1 - r)):
        fill_circle(cx, cy, r, color)


def draw_line(x0, y0, x1, y1, color, width=1):
    """Thick line as a chain of small discs."""
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    rad = max(1, width // 2)
    for i in range(steps + 1):
        t = i / steps
        px = int(round(x0 + (x1 - x0) * t))
        py = int(round(y0 + (y1 - y0) * t))
        fill_circle(px, py, rad, color)


def fill_rot_ellipse(cx, cy, rx, ry, angle_deg, color):
    """Filled ellipse rotated by angle_deg (clockwise, degrees)."""
    th = math.radians(angle_deg)
    co, si = math.cos(th), math.sin(th)
    hw = int(math.sqrt((rx * co) ** 2 + (ry * si) ** 2)) + 1
    hh = int(math.sqrt((rx * si) ** 2 + (ry * co) ** 2)) + 1
    for yy in range(cy - hh, cy + hh + 1):
        for xx in range(cx - hw, cx + hw + 1):
            dx, dy = xx - cx, yy - cy
            u = dx * co + dy * si
            v = -dx * si + dy * co
            if (u / rx) ** 2 + (v / ry) ** 2 <= 1.0:
                _set(xx, yy, color)


# ---------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 characters; '1' is ink, '0' is blank.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    'd': ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01000", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    'h': ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00010", "00000", "00110", "00010", "00010", "00010", "00100"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "00000", "11110", "10001", "10001", "11110", "10000"),
    'q': ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("01000", "01000", "11100", "01000", "01000", "01000", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '·': ("00000", "00000", "00000", "01100", "01100", "00000", "00000"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, color):
    """Draw s with its top-left corner at (x, y)."""
    cx = x
    for ch in s:
        g = FONT.get(ch)
        if g is not None:
            for r in range(7):
                row = g[r]
                for c in range(5):
                    if row[c] == '1':
                        fill_rect(cx + c * scale, y + r * scale,
                                  cx + (c + 1) * scale,
                                  y + (r + 1) * scale, color)
        cx += 6 * scale


def draw_text_centred(cx, y, s, scale, color):
    draw_text(cx - text_width(s, scale) // 2, y, s, scale, color)


# ---------------------------------------------------------------- PNG encode
def _chunk(tag, data):
    return (struct.pack(">I", len(data)) + tag + data +
            struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))


def png_bytes():
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += buf[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
            _chunk(b"IDAT", idat) + _chunk(b"IEND", b""))


# ---------------------------------------------------------------- the shot
def build():
    # studio backdrop: gentle vertical gradient, light grey
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t)
                  for i in range(3))
        fill_rect(0, y, W, y + 1, c)

    # soft contact shadow under the mug
    fill_ellipse(512, 800, 190, 26, SHADOW)
    fill_ellipse(512, 798, 150, 18, SHADOW_DARK)

    # ---- teaspoon, floating tilted to the left of the mug ----
    # handle first, then the bowl on top of it
    draw_line(312, 638, 228, 726, SILVER_DARK, 13)
    draw_line(310, 634, 232, 720, SILVER, 9)
    draw_line(308, 630, 234, 716, SILVER_LIGHT, 4)
    fill_rot_ellipse(300, 600, 27, 43, -28, SILVER_DARK)
    fill_rot_ellipse(300, 600, 24, 40, -28, SILVER)
    fill_rot_ellipse(298, 596, 17, 30, -28, SILVER_LIGHT)
    fill_rot_ellipse(292, 588, 7, 12, -28, (235, 238, 240))

    # ---- the mug ----
    # edge, then the white body on top of it
    fill_rounded_rect(378, 428, 646, 772, 30, MUG_EDGE)
    fill_rounded_rect(380, 430, 644, 770, 28, MUG)
    # handle on the right: ring of white with a dark edge
    fill_ellipse(664, 600, 56, 76, MUG_EDGE)
    fill_ellipse(664, 600, 50, 70, MUG)
    fill_ellipse(668, 600, 30, 50, (226, 226, 224))
    # coffee surface visible inside the rim
    fill_ellipse(512, 438, 112, 24, RIM)
    fill_ellipse(512, 438, 96, 18, COFFEE)
    fill_ellipse(500, 434, 40, 7, COFFEE_LIGHT)

    # ---- gold label band on the mug ----
    fill_rect(392, 560, 632, 642, GOLD)
    fill_rect(392, 560, 632, 564, GOLD_DARK)
    fill_rect(392, 638, 632, 642, GOLD_DARK)
    draw_text_centred(512, 574, "ZERO-G", 4, LABEL_INK)
    draw_text_centred(512, 610, "GRAVITY-FREE MUG", 2, LABEL_INK)

    # ---- the impossible part: coffee that floats ----
    # glossy sphere of coffee hovering above the mug
    fill_circle(512, 322, 58, COFFEE_DARK)
    fill_circle(508, 318, 48, COFFEE)
    fill_circle(490, 300, 20, COFFEE_LIGHT)
    fill_circle(484, 292, 8, CREAM)
    # four droplets frozen mid-air
    for (dx, dy, dr) in ((398, 296, 16), (622, 282, 13),
                         (428, 196, 11), (598, 196, 15)):
        fill_circle(dx, dy, dr, COFFEE)
        fill_circle(dx - dr // 3, dy - dr // 3, max(2, dr // 4),
                    COFFEE_LIGHT)

    # ---- catalogue caption ----
    fill_rect(452, 830, 572, 833, GOLD)
    draw_text_centred(512, 840, "THE ZERO-G MUG", 4, INK)
    draw_text_centred(512, 888, "Coffee that floats. Spills that don't.",
                      3, GREY)
    draw_text_centred(512, 926, "Model ZG-01 · $49.99", 3, GREY_SOFT)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    build()
    path = os.path.join(out_dir, "entry.png")
    data = png_bytes()
    with open(path, "wb") as f:
        f.write(data)
    print("wrote", path, (W, H), len(data), "bytes")


if __name__ == "__main__":
    main()
