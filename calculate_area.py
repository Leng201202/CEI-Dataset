import argparse
import csv
import os
import struct
import subprocess
import tempfile
import zlib
from collections import Counter
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".tif", ".tiff"}


def read_png_pixels(path):
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG file")

    pos = 8
    width = height = bit_depth = color_type = None
    palette = None
    compressed = b""

    while pos < len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        pos += 12 + length

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(
                ">IIBBBBB", chunk
            )
            if bit_depth != 8:
                raise ValueError(f"{path} uses unsupported PNG bit depth {bit_depth}")
            if interlace:
                raise ValueError(f"{path} uses unsupported interlaced PNG encoding")
        elif chunk_type == b"PLTE":
            palette = [tuple(chunk[i : i + 3]) for i in range(0, len(chunk), 3)]
        elif chunk_type == b"IDAT":
            compressed += chunk
        elif chunk_type == b"IEND":
            break

    channels_by_type = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    if color_type not in channels_by_type:
        raise ValueError(f"{path} uses unsupported PNG color type {color_type}")

    channels = channels_by_type[color_type]
    stride = width * channels
    scanlines = zlib.decompress(compressed)
    previous = [0] * stride
    offset = 0

    for _row_index in range(height):
        filter_type = scanlines[offset]
        offset += 1
        row = list(scanlines[offset : offset + stride])
        offset += stride

        for i, value in enumerate(row):
            left = row[i - channels] if i >= channels else 0
            up = previous[i]
            upper_left = previous[i - channels] if i >= channels else 0

            if filter_type == 1:
                row[i] = (value + left) & 255
            elif filter_type == 2:
                row[i] = (value + up) & 255
            elif filter_type == 3:
                row[i] = (value + ((left + up) // 2)) & 255
            elif filter_type == 4:
                predictor = paeth_predictor(left, up, upper_left)
                row[i] = (value + predictor) & 255
            elif filter_type != 0:
                raise ValueError(f"{path} uses unsupported PNG filter {filter_type}")

        for i in range(0, len(row), channels):
            if color_type == 3:
                yield palette[row[i]]
            elif color_type == 0:
                yield (row[i], row[i], row[i])
            elif color_type == 4:
                yield (row[i], row[i], row[i])
            else:
                yield tuple(row[i : i + 3])

        previous = row


def paeth_predictor(left, up, upper_left):
    predictor = left + up - upper_left
    distance_left = abs(predictor - left)
    distance_up = abs(predictor - up)
    distance_upper_left = abs(predictor - upper_left)

    if distance_left <= distance_up and distance_left <= distance_upper_left:
        return left
    if distance_up <= distance_upper_left:
        return up
    return upper_left


def png_size(path):
    data = Path(path).read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG file")
    return struct.unpack(">II", data[16:24])


def tiff_size(path):
    data = Path(path).read_bytes()
    byte_order = data[:2]
    if byte_order == b"II":
        endian = "<"
    elif byte_order == b"MM":
        endian = ">"
    else:
        raise ValueError(f"{path} is not a TIFF file")

    magic = struct.unpack(endian + "H", data[2:4])[0]
    if magic != 42:
        raise ValueError(f"{path} uses unsupported TIFF magic {magic}")

    ifd_offset = struct.unpack(endian + "I", data[4:8])[0]
    entry_count = struct.unpack(endian + "H", data[ifd_offset : ifd_offset + 2])[0]
    width = height = None

    for index in range(entry_count):
        offset = ifd_offset + 2 + index * 12
        tag, field_type, count = struct.unpack(endian + "HHI", data[offset : offset + 8])
        value_bytes = data[offset + 8 : offset + 12]

        if tag not in {256, 257}:
            continue

        if field_type == 3:
            value = struct.unpack(endian + "H", value_bytes[:2])[0]
        elif field_type == 4:
            value = struct.unpack(endian + "I", value_bytes)[0]
        else:
            raise ValueError(f"{path} has unsupported TIFF dimension field type {field_type}")

        if count != 1:
            raise ValueError(f"{path} has unsupported TIFF dimension count {count}")
        if tag == 256:
            width = value
        else:
            height = value

    if width is None or height is None:
        raise ValueError(f"{path} is missing TIFF width/height tags")

    return width, height


def image_size(path):
    suffix = path.suffix.lower()
    if suffix == ".png":
        return png_size(path)
    if suffix in {".tif", ".tiff"}:
        return tiff_size(path)
    raise ValueError(f"Unsupported image extension: {path.suffix}")


def convert_tiff_with_sips(path, output_path):
    subprocess.run(
        ["sips", "-s", "format", "png", str(path), "--out", str(output_path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def mask_color_counts(path):
    suffix = path.suffix.lower()
    if suffix == ".png":
        converted_path = path
        return Counter(read_png_pixels(converted_path)), png_size(converted_path)

    if suffix in {".tif", ".tiff"}:
        with tempfile.TemporaryDirectory() as temp_dir:
            converted_path = Path(temp_dir) / f"{path.stem}.png"
            convert_tiff_with_sips(path, converted_path)
            return Counter(read_png_pixels(converted_path)), png_size(converted_path)

    raise ValueError(f"Unsupported image extension: {path.suffix}")


def iter_masks(input_path, pattern):
    input_path = Path(input_path)
    if input_path.is_file():
        yield input_path
        return

    for path in sorted(input_path.glob(pattern)):
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def area_row(path, pixel_size_m, background):
    counts, (width, height) = mask_color_counts(path)
    total_pixels = width * height

    if background == "dominant":
        background_color, background_pixels = counts.most_common(1)[0]
    elif background == "black":
        background_color = (0, 0, 0)
        background_pixels = counts.get(background_color, 0)
    else:
        background_color = tuple(int(part) for part in background.split(","))
        background_pixels = counts.get(background_color, 0)

    area_pixels = total_pixels - background_pixels
    area_m2 = area_pixels * pixel_size_m * pixel_size_m
    area_km2 = area_m2 / 1_000_000

    return {
        "file": str(path),
        "width": width,
        "height": height,
        "total_pixels": total_pixels,
        "background_rgb": ",".join(str(v) for v in background_color),
        "background_pixels": background_pixels,
        "area_pixels": area_pixels,
        "pixel_size_m": pixel_size_m,
        "area_m2": area_m2,
        "area_km2": area_km2,
    }


def full_image_area_row(path, pixel_size_m):
    width, height = image_size(path)
    total_pixels = width * height
    area_m2 = total_pixels * pixel_size_m * pixel_size_m
    area_km2 = area_m2 / 1_000_000

    return {
        "file": str(path),
        "width": width,
        "height": height,
        "total_pixels": total_pixels,
        "pixel_size_m": pixel_size_m,
        "area_m2": area_m2,
        "area_km2": area_km2,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate mask area in pixels, square meters, and square kilometers."
    )
    parser.add_argument("input", help="Mask file or directory containing mask images.")
    parser.add_argument("--pattern", default="*_mask.tif", help="Glob pattern when input is a directory.")
    parser.add_argument(
        "--full-image",
        action="store_true",
        help="Calculate the area of each entire image instead of counting non-background mask pixels.",
    )
    parser.add_argument(
        "--pixel-size-m",
        type=float,
        required=True,
        help="Ground size of one pixel edge in meters. Example: 10 for Sentinel-2 10 m pixels.",
    )
    parser.add_argument(
        "--background",
        default="dominant",
        help="Background color: dominant, black, or an RGB triplet like 0,69,255.",
    )
    parser.add_argument("--output", help="Optional CSV output path.")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.full_image:
        rows = [full_image_area_row(path, args.pixel_size_m) for path in iter_masks(args.input, args.pattern)]
    else:
        rows = [area_row(path, args.pixel_size_m, args.background) for path in iter_masks(args.input, args.pattern)]

    if not rows:
        raise SystemExit("No mask files found.")

    fieldnames = list(rows[0])
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    writer = csv.DictWriter(os.sys.stdout, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)


if __name__ == "__main__":
    main()
