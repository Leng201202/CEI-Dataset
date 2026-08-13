"""Create side-by-side PNG previews of satellite images and TIFF masks.

The GIMP-authored masks are deflate-compressed TIFFs that most quick-look
tools and browsers won't render inline. This pairs each ``*_mask.tif`` with
the corresponding ``*_image.png`` and writes a combined PNG to the gitignored
preview folder (data/raw/review_preview/). The satellite image is on the left
and the mask is on the right. The source files are never modified.

    python tif_to_png.py                          # preview every pair under data/raw/review
    python tif_to_png.py --input path/to/one_mask.tif
"""

import argparse
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = REPO_ROOT / "data" / "raw" / "review"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "raw" / "review_preview"


def iter_masks(input_path, pattern):
    """Accept either a single file or a folder to glob."""
    if input_path.is_file():
        return [input_path]
    return sorted(input_path.glob(pattern))


def matching_image_path(mask_path):
    """Return the satellite image expected to accompany a mask."""
    if not mask_path.stem.endswith("_mask"):
        raise ValueError(f"Mask filename must end with '_mask': {mask_path.name}")
    pair_stem = mask_path.stem.removesuffix("_mask")
    return mask_path.with_name(f"{pair_stem}_image.png")


def convert(mask_path, output_dir):
    """Write one satellite/mask comparison PNG and return its path."""
    image_path = matching_image_path(mask_path)
    if not image_path.is_file():
        raise FileNotFoundError(
            f"Satellite image not found for {mask_path.name}: expected {image_path}"
        )

    pair_stem = mask_path.stem.removesuffix("_mask")
    out_path = output_dir / f"{pair_stem}_review.png"

    with Image.open(image_path) as satellite_source, Image.open(mask_path) as mask_source:
        satellite = satellite_source.convert("RGB")
        mask = mask_source.convert("RGB")

        if satellite.size != mask.size:
            raise ValueError(
                f"Image size mismatch for {pair_stem}: "
                f"satellite is {satellite.size}, mask is {mask.size}"
            )

        width, height = satellite.size
        comparison = Image.new("RGB", (width * 2, height))
        comparison.paste(satellite, (0, 0))
        comparison.paste(mask, (width, 0))
        comparison.save(out_path)

    return out_path


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", default=DEFAULT_INPUT, type=Path, help="A .tif file, or a folder of them.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, help="Where to write PNG previews.")
    parser.add_argument("--pattern", default="*_mask.tif", help="Glob used when --input is a folder.")
    return parser.parse_args()


def main():
    args = parse_args()
    masks = iter_masks(args.input, args.pattern)
    if not masks:
        raise SystemExit(f"No files matching {args.pattern!r} in {args.input}")

    args.output.mkdir(parents=True, exist_ok=True)

    for path in masks:
        out_path = convert(path, args.output)
        try:
            shown = out_path.relative_to(REPO_ROOT)
        except ValueError:
            shown = out_path
        print(f"ok   {path.name} + {matching_image_path(path).name} -> {shown}")

    print(f"\n{len(masks)} side-by-side preview(s) created")


if __name__ == "__main__":
    main()
