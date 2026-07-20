"""Convert hand-edited RGB masks into single-channel class-ID label masks.

The RGB masks in data/raw/review/ are the source of truth -- they are what you
edit in GIMP. This script is the build step that turns them into the integer
labels a segmentation model actually trains on. It is safe to re-run at any
time; it only ever writes to the output directory.

The colour <-> ID mapping lives in classes.json so the exporter, the dataloader,
and the GIMP palette all read from one place.

Any pixel whose colour is not an exact match for a class is a labelling error
(usually an anti-aliased edge from painting with the Paintbrush instead of the
Pencil). Those are reported and the file is skipped rather than silently
snapped to the nearest class, which would bake invisible noise into training.

    python rgb_to_class_id.py --check          # validate only, write nothing
    python rgb_to_class_id.py                  # export to data/masks
    python rgb_to_class_id.py --stats          # export and print class balance
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_CLASSES = REPO_ROOT / "classes.json"
DEFAULT_INPUT = REPO_ROOT / "data" / "raw" / "review"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "masks"


def load_classes(path):
    spec = json.loads(Path(path).read_text(encoding="utf-8"))
    color_to_id = {}
    id_to_name = {}

    for entry in spec["classes"]:
        color = tuple(entry["color"])
        if color in color_to_id:
            raise ValueError(f"Colour {color} is assigned to more than one class in {path}")
        if entry["id"] > 255:
            raise ValueError(f"Class id {entry['id']} does not fit in a uint8 mask")
        color_to_id[color] = entry["id"]
        id_to_name[entry["id"]] = entry["name"]

    return color_to_id, id_to_name, spec


def build_lookup(color_to_id):
    """Flat 2**24 -> id table, so conversion is one vectorised index per mask."""
    lookup = np.full(1 << 24, 255, dtype=np.uint8)
    for (r, g, b), class_id in color_to_id.items():
        lookup[(r << 16) | (g << 8) | b] = class_id
    return lookup


def convert(path, lookup):
    """Return (label array, {unknown rgb: count}). Label is uint8, 255 = unmatched."""
    with Image.open(path) as im:
        rgb = np.array(im.convert("RGB"))

    packed = (
        rgb[:, :, 0].astype(np.uint32) << 16
        | rgb[:, :, 1].astype(np.uint32) << 8
        | rgb[:, :, 2].astype(np.uint32)
    )
    label = lookup[packed]

    unknown = {}
    bad = label == 255
    if bad.any():
        colors, counts = np.unique(rgb[bad].reshape(-1, 3), axis=0, return_counts=True)
        unknown = {tuple(int(v) for v in c): int(n) for c, n in zip(colors, counts)}

    return label, unknown


# Colours that used to be classes. Seeing one means somebody is painting from an
# outdated palette, which is a different fix from a stray anti-aliased pixel.
RETIRED = {
    (148, 148, 148): "Developed space -- retired, merged into Non-Vegetated",
}


def nearest_class(color, color_to_id, id_to_name):
    """Closest palette entry to an off-palette colour, as a hint for the fix.

    Purely advisory -- nothing is ever snapped to this. An anti-aliased edge
    lands between two classes, so the nearest one is usually what was intended.
    """
    r, g, b = color
    best = min(color_to_id, key=lambda c: (c[0] - r) ** 2 + (c[1] - g) ** 2 + (c[2] - b) ** 2)
    distance = max(abs(best[0] - r), abs(best[1] - g), abs(best[2] - b))
    return id_to_name[color_to_id[best]], distance


def iter_masks(input_path, pattern):
    """Accept either a single mask or a folder to glob."""
    if input_path.is_file():
        return [input_path]
    return sorted(input_path.glob(pattern))


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", default=DEFAULT_INPUT, type=Path, help="A mask file, or a folder of them.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path, help="Where to write class-ID masks.")
    parser.add_argument("--classes", default=DEFAULT_CLASSES, type=Path, help="Class definition JSON.")
    parser.add_argument("--pattern", default="*_mask.tif", help="Glob for the RGB masks.")
    parser.add_argument("--suffix", default="_label.png", help="Replaces '_mask.tif' in output names.")
    parser.add_argument("--check", action="store_true", help="Validate palette only; write nothing.")
    parser.add_argument("--stats", action="store_true", help="Print per-class pixel counts across the run.")
    return parser.parse_args()


def main():
    args = parse_args()
    color_to_id, id_to_name, spec = load_classes(args.classes)
    lookup = build_lookup(color_to_id)

    masks = iter_masks(args.input, args.pattern)
    if not masks:
        raise SystemExit(f"No masks matching {args.pattern!r} in {args.input}")

    if not args.check:
        args.output.mkdir(parents=True, exist_ok=True)

    totals = {}
    failed = []

    for path in masks:
        label, unknown = convert(path, lookup)

        if unknown:
            failed.append((path, unknown))
            total_bad = sum(unknown.values())
            print(f"FAIL {path.name}: {total_bad:,} off-palette px in {len(unknown)} colour(s)")
            for color, count in sorted(unknown.items(), key=lambda kv: -kv[1])[:5]:
                if color in RETIRED:
                    note = RETIRED[color]
                else:
                    name, distance = nearest_class(color, color_to_id, id_to_name)
                    note = (
                        f"nearest: {name} (anti-aliased edge)"
                        if distance <= 8
                        else f"nearest: {name}, but not close -- check this one"
                    )
                print(f"       {str(color):18s} x{count:<9,d} {note}")
            if len(unknown) > 5:
                print(f"       ... and {len(unknown) - 5} more colour(s)")
            continue

        ids, counts = np.unique(label, return_counts=True)
        for class_id, count in zip(ids, counts):
            totals[int(class_id)] = totals.get(int(class_id), 0) + int(count)

        if args.check:
            print(f"ok   {path.name}")
            continue

        out_path = args.output / (path.name.replace("_mask.tif", "") + args.suffix)
        Image.fromarray(label, mode="L").save(out_path, optimize=True)
        print(f"ok   {path.name} -> {out_path.relative_to(REPO_ROOT)}")

    print()
    verb = "checked" if args.check else "converted"
    print(f"{len(masks) - len(failed)}/{len(masks)} masks {verb}")

    if args.stats and totals:
        grand = sum(totals.values())
        print(f"\nClass balance across {len(masks) - len(failed)} masks:")
        for class_id, count in sorted(totals.items(), key=lambda kv: -kv[1]):
            name = id_to_name.get(class_id, "UNMATCHED")
            print(f"  {class_id}  {name:15s} {count:13,d}  {100 * count / grand:5.2f}%")

    if failed:
        print(
            f"\n{len(failed)} mask(s) contain colours that are not classes. Repaint those "
            f"regions with the Pencil (not the Paintbrush) using the {len(color_to_id)} "
            f"palette colours, then re-run. Nothing was written for them.",
            file=sys.stderr,
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
