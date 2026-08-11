"""Generate the POLIS repository banner (assets/banner.png) and social preview
(assets/social_preview.png) from the gradient-ramp palette.
Run: python3 assets/make_banner.py
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

CREAM = (247, 243, 232)
INK = (47, 47, 49)          # stone 2F2F31
MUTED = (110, 110, 115)     # stone 6E6E73

RAMPS = {
    "cucumber": ["E2E8D4", "CFD885", "BBC896", "A8B977", "889A51", "606D3B", "384023"],
    "strawberry": ["F4CAC9", "EDA5A4", "E67F7E", "E15957", "DC312F", "9F1F1E", "5B1413"],
    "grapefruit": ["F6D5C7", "F0B79F", "EB9977", "E07041", "BF5022", "863A1A", "4F2311"],
    "mint": ["CFDED0", "AAC6AD", "89AF8D", "68976D", "527855", "3B543E", "243326"],
    "cocoa": ["E4D5CE", "D9B6AA", "AA7760", "8A5C48", "664434", "553527", "422B21"],
    "lemon": ["F6F0DA", "F1E8C5", "EDE0B0", "E8D89B", "E4D085", "C9A932", "6E5E1E"],
    "stone": ["DBDBDC", "C1C1C4", "A8A8AB", "8E8E93", "6E6E73", "4E4E52", "2F2F31"],
}

SERIF = "/System/Library/Fonts/Supplemental/Georgia.ttf"
SERIF_ITALIC = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"
SANS = "/System/Library/Fonts/Helvetica.ttc"


def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def make(width, height, out, title_px, sub_px, tag_px):
    img = Image.new("RGB", (width, height), CREAM)
    d = ImageDraw.Draw(img)

    title_f = ImageFont.truetype(SERIF, title_px)
    sub_f = ImageFont.truetype(SERIF_ITALIC, sub_px)
    tag_f = ImageFont.truetype(SANS, tag_px)

    # Right: seven horizontal gradient ramps of rounded tiles.
    rows = len(RAMPS)
    tile_h = int(height * 0.072)
    row_gap = int(tile_h * 0.5)
    block_h = rows * tile_h + (rows - 1) * row_gap
    y0 = (height - block_h) // 2
    tile_w = int(tile_h * 1.9)
    tile_gap = int(tile_h * 0.22)
    block_w = 7 * tile_w + 6 * tile_gap
    x0 = width - block_w - int(height * 0.16)
    for r, ramp in enumerate(RAMPS.values()):
        y = y0 + r * (tile_h + row_gap)
        for c, hx in enumerate(ramp):
            x = x0 + c * (tile_w + tile_gap)
            d.rounded_rectangle([x, y, x + tile_w, y + tile_h],
                                radius=max(3, tile_h // 6), fill=hex2rgb(hx))

    # Left: serif wordmark and italic subtitle, like the palette card.
    lx = int(height * 0.18)
    ly = int(height * 0.24)
    d.text((lx, ly), "POLIS", font=title_f, fill=INK)
    ly += title_px + int(sub_px * 0.45)
    d.text((lx, ly), "multi-agent planning on real geography", font=sub_f, fill=MUTED)
    ly += sub_px + int(sub_px * 0.85)
    tagline = "S E N S E   ·   N E G O T I A T E   ·   G O V E R N"
    d.text((lx, ly), tagline, font=tag_f, fill=hex2rgb("889A51"))
    ly += tag_px + int(tag_px * 1.1)
    d.text((lx, ly), "Chicago  ·  London  ·  Suzhou — three frozen-OSM cases",
           font=tag_f, fill=MUTED)

    # Bottom hairline strip: the seven base tones.
    strip_h = max(5, height // 66)
    bases = ["A8B977", "DC312F", "EB9977", "AAC6AD", "AA7760", "E4D085", "8E8E93"]
    seg = width / len(bases)
    for k, hx in enumerate(bases):
        d.rectangle([k * seg, height - strip_h, (k + 1) * seg, height], fill=hex2rgb(hx))

    img.save(out)
    print("wrote", out, img.size)


if __name__ == "__main__":
    make(1600, 400, "assets/banner.png", title_px=84, sub_px=30, tag_px=17)
    make(1280, 640, "assets/social_preview.png", title_px=110, sub_px=40, tag_px=23)
