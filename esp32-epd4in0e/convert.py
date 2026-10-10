"""
Run this on your COMPUTER (not the board).

Turns any picture into a .bin file the 4inch e-Paper HAT+ (E) can show:
  - resizes/crops it to 400 x 600 (rotates landscape photos to fill the portrait screen)
  - reduces it to the panel's 6 colours with dithering
  - packs 2 pixels per byte, the format the display expects

Usage:
  pip install pillow
  python convert.py my_photo.jpg            -> writes my_photo.bin
  python convert.py my_photo.jpg --no-rotate --saturation 1.5
  python convert.py --source ./photos --target ./bins
"""
import argparse
import os
from PIL import Image, ImageEnhance, ImageOps

WIDTH, HEIGHT = 400, 600

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff"}

# Panel colours, in palette order, and the 4-bit code the panel uses for each
PALETTE = [
    ((0, 0, 0),       0x0),  # black
    ((255, 255, 255), 0x1),  # white
    ((255, 255, 0),   0x2),  # yellow
    ((255, 0, 0),     0x3),  # red
    ((0, 0, 255),     0x5),  # blue
    ((0, 255, 0),     0x6),  # green
]


def convert(src, dst, rotate=True, saturation=1.3, dither=True):
    img = Image.open(src)
    img = ImageOps.exif_transpose(img).convert("RGB")

    # Landscape photo on a portrait screen: turn it sideways so it fills the panel
    if rotate and img.width > img.height:
        img = img.rotate(90, expand=True)

    # Scale and centre-crop to exactly 400 x 600
    img = ImageOps.fit(img, (WIDTH, HEIGHT), Image.LANCZOS)

    # The panel's colours are muted, so a bit of extra saturation helps
    if saturation != 1.0:
        img = ImageEnhance.Color(img).enhance(saturation)

    pal_img = Image.new("P", (1, 1))
    flat = []
    for rgb, _ in PALETTE:
        flat.extend(rgb)
    flat += list(PALETTE[0][0]) * (256 - len(PALETTE))   # pad with black
    pal_img.putpalette(flat)

    q = img.quantize(palette=pal_img,
                     dither=Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE)
    idx = q.tobytes()

    codes = [c for _, c in PALETTE]
    out = bytearray(WIDTH * HEIGHT // 2)
    for i in range(0, len(idx), 2):
        hi = codes[idx[i]] if idx[i] < len(codes) else 0
        lo = codes[idx[i + 1]] if idx[i + 1] < len(codes) else 0
        out[i // 2] = (hi << 4) | lo

    with open(dst, "wb") as f:
        f.write(out)

    # Also save a preview so you can see what it'll look like before uploading
    preview = os.path.splitext(dst)[0] + "_preview.png"
    q.convert("RGB").save(preview)
    print("wrote %s (%d bytes) and %s" % (dst, len(out), preview))


def iter_source_images(source_dir):
    source_dir = os.path.abspath(source_dir)
    for root, _, names in os.walk(source_dir):
        for name in sorted(names):
            if os.path.splitext(name)[1].lower() in IMAGE_EXTENSIONS:
                yield os.path.join(root, name)


def target_bin_path(source_root, target_root, src_path):
    rel = os.path.relpath(src_path, source_root)
    base, _ = os.path.splitext(rel)
    return os.path.join(target_root, base + ".bin")


def convert_tree(source_dir, target_dir, rotate=True, saturation=1.3, dither=True):
    source_dir = os.path.abspath(source_dir)
    target_dir = os.path.abspath(target_dir)
    converted = skipped = 0

    for src in iter_source_images(source_dir):
        dst = target_bin_path(source_dir, target_dir, src)
        if os.path.isfile(dst):
            print("skip (exists): %s" % dst)
            skipped += 1
            continue
        os.makedirs(os.path.dirname(dst) or target_dir, exist_ok=True)
        convert(src, dst, rotate=rotate, saturation=saturation, dither=dither)
        converted += 1

    print("done: %d converted, %d skipped" % (converted, skipped))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image", nargs="?", help="single image file")
    ap.add_argument("-s", "--source", help="walk this directory for images to convert")
    ap.add_argument("-t", "--target", help="write .bin files here (mirrors source layout)")
    ap.add_argument("-o", "--output", help="output .bin for single-file mode (default: same name as image)")
    ap.add_argument("--no-rotate", action="store_true", help="don't rotate landscape images")
    ap.add_argument("--saturation", type=float, default=1.3)
    ap.add_argument("--no-dither", action="store_true")
    a = ap.parse_args()

    rotate = not a.no_rotate
    dither = not a.no_dither

    if a.source:
        if not a.target:
            ap.error("--target is required when using --source")
        if a.image:
            ap.error("use either a single image or --source/--target, not both")
        convert_tree(a.source, a.target, rotate=rotate, saturation=a.saturation, dither=dither)
    elif a.image:
        out = a.output or os.path.splitext(a.image)[0] + ".bin"
        convert(a.image, out, rotate=rotate, saturation=a.saturation, dither=dither)
    else:
        ap.error("provide an image path or --source and --target")