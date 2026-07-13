import argparse
import re
from pathlib import Path

from PIL import Image


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
MAESUAI_PATTERN = re.compile(r"^ms_(\d+)(_real)?$")


def crop_tiles(img, cropx, cropy, left_margin=260):
    w, h = img.size
    tiles = []
    usable_w = w - left_margin
    n_x = usable_w // cropx
    n_y = h // cropy

    for i in range(n_x):
        for j in range(n_y):
            left = left_margin + i * cropx
            upper = j * cropy
            right = left + cropx
            lower = upper + cropy
            if right <= w and lower <= h:
                tile = img.crop((left, upper, right, lower))
                tiles.append(((i, j), tile))

    return tiles


def output_stem(source_stem):
    # Keep historical names like ms_001_0000.png for inputs named ms_1.png.
    parts = source_stem.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return f"{parts[0]}_{int(parts[1]):03d}"
    return source_stem


def iter_images(input_dir, only=None):
    only_names = set(only or [])
    for path in sorted(input_dir.iterdir()):
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if only_names and path.name not in only_names and path.stem not in only_names:
            continue
        yield path


def maesuai_sort_key(path):
    match = MAESUAI_PATTERN.match(path.stem)
    if match:
        return int(match.group(1))
    return path.stem


def iter_maesuai_images(input_dir, real=False):
    wanted_real = "_real" if real else None
    paths = []
    for path in input_dir.iterdir():
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        match = MAESUAI_PATTERN.match(path.stem)
        if not match:
            continue
        if match.group(2) == wanted_real:
            paths.append(path)

    yield from sorted(paths, key=maesuai_sort_key)


def save_tiles_for_sources(sources, output_dir, name_prefix, start_index, crop_size, left_margin):
    output_dir.mkdir(parents=True, exist_ok=True)
    out_idx = start_index

    for in_path in sources:
        try:
            with Image.open(in_path) as img:
                if img.width < crop_size + left_margin or img.height < crop_size:
                    print(f"Skipping {in_path.name}: image too small for cropping with left margin.")
                    continue

                tiles = crop_tiles(img, crop_size, crop_size, left_margin)
                if not tiles:
                    print(f"No tiles created for {in_path.name}.")
                    continue

                for _tile_pos, tile in tiles:
                    out_path = output_dir / f"{name_prefix}_{out_idx}.tif"
                    if tile.mode == "RGBA":
                        tile = tile.convert("RGB")
                    tile.save(out_path)
                    print(f"Saved tile: {out_path}")
                    out_idx += 1
        except Exception as exc:
            print(f"Error processing {in_path.name}: {exc}")

    return out_idx


def crop_maesuai_dataset(input_dir, label_dir, real_dir, crop_size=1024, left_margin=260, name_prefix="maesuai"):
    input_dir = Path(input_dir)
    label_dir = Path(label_dir)
    real_dir = Path(real_dir)

    label_sources = list(iter_maesuai_images(input_dir, real=False))
    real_sources = list(iter_maesuai_images(input_dir, real=True))

    next_label = save_tiles_for_sources(
        label_sources,
        label_dir,
        name_prefix,
        start_index=1,
        crop_size=crop_size,
        left_margin=left_margin,
    )
    next_real = save_tiles_for_sources(
        real_sources,
        real_dir,
        name_prefix,
        start_index=1,
        crop_size=crop_size,
        left_margin=left_margin,
    )

    return next_label - 1, next_real - 1


def crop_images_in_folder(input_dir, output_dir, crop_size=1024, left_margin=260, only=None):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    for in_path in iter_images(input_dir, only):
        try:
            with Image.open(in_path) as img:
                if img.width < crop_size + left_margin or img.height < crop_size:
                    print(f"Skipping {in_path.name}: image too small for cropping with left margin.")
                    continue

                tiles = crop_tiles(img, crop_size, crop_size, left_margin)
                if not tiles:
                    print(f"No tiles created for {in_path.name}.")
                    continue

                stem = output_stem(in_path.stem)
                for tile_idx, ((_i, _j), tile) in enumerate(tiles):
                    out_name = f"{stem}_{tile_idx:04d}{in_path.suffix.lower()}"
                    out_path = output_dir / out_name
                    tile.save(out_path)
                    print(f"Saved tile: {out_path}")
                    total += 1
        except Exception as exc:
            print(f"Error processing {in_path.name}: {exc}")

    return total


def parse_args():
    parser = argparse.ArgumentParser(description="Crop source images into square tiles.")
    parser.add_argument(
        "--mode",
        choices=("standard", "maesuai"),
        default="maesuai",
        help="Use 'maesuai' to split ms_N and ms_N_real crops into label/real TIFF directories.",
    )
    parser.add_argument("--input-dir", default="data/raw/Images")
    parser.add_argument("--output-dir", default="data/raw/output/images")
    parser.add_argument("--label-dir", default="data/raw/cropped/label")
    parser.add_argument("--real-dir", default="data/raw/cropped/real")
    parser.add_argument("--name-prefix", default="maesuai")
    parser.add_argument("--crop-size", type=int, default=1024)
    parser.add_argument("--left-margin", type=int, default=260)
    parser.add_argument(
        "--only",
        action="append",
        help="Process only this file name or stem. Can be passed more than once.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.mode == "maesuai":
        label_count, real_count = crop_maesuai_dataset(
            args.input_dir,
            args.label_dir,
            args.real_dir,
            crop_size=args.crop_size,
            left_margin=args.left_margin,
            name_prefix=args.name_prefix,
        )
        print(f"Created {label_count} label tile(s) and {real_count} real tile(s).")
    else:
        count = crop_images_in_folder(
            args.input_dir,
            args.output_dir,
            crop_size=args.crop_size,
            left_margin=args.left_margin,
            only=args.only,
        )
        print(f"Created {count} tile(s).")
