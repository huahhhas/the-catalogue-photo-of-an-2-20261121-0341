"""THE ZERO-G MUG — catalogue photograph of an impossible gadget.

A ceramic mug on a clean studio background. Above it hovers a glossy
sphere of coffee, suspended mid-air, with small droplets frozen between
the sphere and the mug. One accessory only: a single teaspoon floating
tilted beside the mug. The joke reads at a glance: coffee that floats,
so it can never spill.

Deterministic, stdlib + Pillow only, no network.
Writes one 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png.
"""

import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vertical_gradient(img, top, bottom, y0=0, y1=None):
    """Paint a smooth vertical gradient over the whole canvas."""
    y1 = y1 if y1 is not None else img.height
    d = ImageDraw.Draw(img)
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        d.line([(0, y), (img.width, y)], fill=lerp(top, bottom, t))


def soft_shadow(base, box, blur, alpha):
    """Blurred dark ellipse on its own layer, composited onto base."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse(box, fill=(30, 28, 26, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(layer)


def gloss_sphere(base, cx, cy, r, dark, mid, light):
    """A glossy sphere: concentric circles shaded toward top-left light."""
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    steps = 48
    for i in range(steps, 0, -1):
        t = i / steps  # 1 at edge, 0 at centre
        if t > 0.55:
            col = lerp(mid, dark, (t - 0.55) / 0.45)
        else:
            col = lerp(light, mid, t / 0.55)
        # shading centre pulled toward the top-left (light direction)
        ox = -int(r * 0.28 * (1 - t))
        oy = -int(r * 0.30 * (1 - t))
        rr = r * i / steps
        d.ellipse([cx + ox - rr, cy + oy - rr, cx + ox + rr, cy + oy + rr],
                  fill=col + (255,))
    # crisp white specular highlight, top-left
    hl = Image.new("RGBA", base.size, (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse([cx - r * 0.62, cy - r * 0.72, cx - r * 0.05, cy - r * 0.18],
               fill=(255, 255, 255, 235))
    hl = hl.filter(ImageFilter.GaussianBlur(r * 0.12))
    layer.alpha_composite(hl)
    base.alpha_composite(layer)


def draw_spoon(base):
    """One teaspoon, floating tilted ~30 degrees left of the mug.

    Drawn directly in place (no layer rotation) so the bowl lands exactly
    clear of the mug and its label: bowl centre (250, 560), handle
    rising to the upper left.
    """
    d = ImageDraw.Draw(base)
    # faint displaced shadow under the spoon, on the background
    soft_shadow(base, [110, 622, 320, 650], blur=14, alpha=70)
    d = ImageDraw.Draw(base)
    # handle: thick metallic bar from the bowl up to the left
    d.line([(212, 542), (96, 482)], fill=(178, 182, 188, 255), width=26)
    d.line([(208, 534), (100, 476)], fill=(226, 229, 233, 255), width=7)
    # rounded tip of the handle
    d.ellipse([83, 469, 109, 495], fill=(200, 204, 209, 255))
    # bowl: outer rim, inner dish, bright centre
    d.ellipse([188, 506, 314, 616], fill=(150, 155, 162, 255))
    d.ellipse([200, 518, 302, 604], fill=(196, 200, 206, 255))
    d.ellipse([214, 530, 288, 592], fill=(168, 173, 180, 255))
    d.ellipse([222, 536, 272, 572], fill=(240, 242, 245, 220))


def draw_mug(base):
    """White ceramic mug with coffee surface, handle and label band."""
    d = ImageDraw.Draw(base)
    # handle first, on the right: the body then covers the join
    d.ellipse([648, 552, 778, 692], outline=(202, 200, 196, 255), width=30)
    d.arc([648, 552, 778, 692], start=300, end=90,
          fill=(168, 166, 162, 255), width=30)
    # body: rounded rectangle, white ceramic
    body = [330, 500, 694, 758]
    d.rounded_rectangle(body, radius=26, fill=(250, 250, 248, 255))
    # subtle vertical shading: darker toward the right edge
    shade = Image.new("RGBA", base.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for x in range(330, 695):
        t = (x - 330) / 364.0
        a = int(58 * t * t)
        sd.line([(x, 506), (x, 752)], fill=(120, 118, 112, a))
    base.alpha_composite(shade)
    d = ImageDraw.Draw(base)
    # soft left-edge highlight strip (light from top-left)
    d.rounded_rectangle([330, 500, 352, 758], radius=20,
                        fill=(255, 255, 255, 255))
    d.rectangle([330, 520, 352, 738], fill=(255, 255, 255, 255))
    # rim: outer ellipse, then dark coffee surface inside
    d.ellipse([330, 478, 694, 528], fill=(246, 246, 244, 255))
    d.ellipse([344, 484, 680, 522], fill=(58, 32, 14, 255))
    d.ellipse([352, 488, 672, 518], fill=(74, 42, 18, 255))
    # coffee sheen arc on the surface
    d.arc([360, 488, 664, 518], start=200, end=330,
          fill=(150, 96, 52, 255), width=5)
    # redraw body right edge over the handle's inner join so it reads as one piece
    d.rounded_rectangle([330, 500, 694, 758], radius=26,
                        outline=(226, 224, 220, 255), width=2)
    # label band across the mug
    d.rectangle([330, 592, 694, 676], fill=(38, 52, 66, 255))
    d.rectangle([330, 592, 694, 598], fill=(212, 164, 74, 255))
    d.rectangle([330, 670, 694, 676], fill=(212, 164, 74, 255))
    f_big = font(42, bold=True)
    f_small = font(18, bold=True)
    d.text((512, 606), "ZERO-G", font=f_big, fill=(250, 250, 248, 255),
           anchor="ma")
    d.text((512, 646), "G R A V I T Y - F R E E   M U G", font=f_small,
           fill=(212, 164, 74, 255), anchor="ma")


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)

    img = Image.new("RGBA", (W, H), (232, 233, 235, 255))
    # studio backdrop: light-grey gradient, slightly darker floor below y=760
    vertical_gradient(img, (236, 237, 239), (214, 215, 218), 0, 760)
    vertical_gradient(img, (208, 209, 212), (192, 194, 197), 760, H)
    d = ImageDraw.Draw(img)
    d.line([(0, 760), (W, 760)], fill=(186, 188, 191, 255), width=3)

    # contact shadow under the mug (soft, offset down-right from top-left light)
    soft_shadow(img, [330, 748, 730, 792], blur=16, alpha=110)

    # floating coffee sphere — the impossible part, hero of the shot
    gloss_sphere(img, 512, 336, 96,
                 dark=(46, 24, 10), mid=(104, 58, 26), light=(168, 106, 58))

    # droplets frozen between sphere and mug
    gloss_sphere(img, 452, 452, 16,
                 dark=(46, 24, 10), mid=(104, 58, 26), light=(168, 106, 58))
    gloss_sphere(img, 512, 440, 21,
                 dark=(46, 24, 10), mid=(104, 58, 26), light=(168, 106, 58))
    gloss_sphere(img, 574, 456, 13,
                 dark=(46, 24, 10), mid=(104, 58, 26), light=(168, 106, 58))
    gloss_sphere(img, 540, 472, 9,
                 dark=(46, 24, 10), mid=(104, 58, 26), light=(168, 106, 58))

    draw_mug(img)
    draw_spoon(img)

    # catalogue caption, bottom, dark charcoal
    d = ImageDraw.Draw(img)
    d.text((512, 836), "THE ZERO-G MUG", font=font(46, bold=True),
           fill=(44, 44, 46, 255), anchor="ma")
    d.text((512, 896), "Coffee that floats. Spills that don't.",
           font=font(30), fill=(74, 74, 76, 255), anchor="ma")
    d.text((512, 946), "Model ZG-01  ·  $49.99",
           font=font(22), fill=(110, 110, 113, 255), anchor="ma")

    img.convert("RGB").save(os.path.join(out_dir, "entry.png"),
                            format="PNG", optimize=True)


if __name__ == "__main__":
    main()
