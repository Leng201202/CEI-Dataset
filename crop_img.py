# Crop images in a directory to 1024x1024 pixels (center crop)
import os
from PIL import Image


def crop_tiles(img, cropx, cropy, left_margin=260):
	w, h = img.size
	tiles = []
	# Adjust width for left margin
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

def crop_images_in_folder(input_dir, output_dir, crop_size=1024, left_margin=100):
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	tile_idx = 0
	for fname in os.listdir(input_dir):
		if fname.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")):
			in_path = os.path.join(input_dir, fname)
			try:
				with Image.open(in_path) as img:
					if img.width < crop_size + left_margin or img.height < crop_size:
						print(f"Skipping {fname}: image too small for cropping with left margin.")
						continue
					tiles = crop_tiles(img, crop_size, crop_size, left_margin)
					if not tiles:
						print(f"No tiles created for {fname}.")
						continue
					ext = os.path.splitext(fname)[1]
					for (i, j), tile in tiles:
						out_name = f"dataset_{tile_idx:04d}{ext}"
						out_path = os.path.join(output_dir, out_name)
						tile.save(out_path)
						print(f"Saved tile: {out_path}")
						tile_idx += 1
			except Exception as e:
				print(f"Error processing {fname}: {e}")

if __name__ == "__main__":
	# Fixed input and output directories
	input_dir = os.path.join("data", "raw", "image")
	output_dir = os.path.join("data", "raw", "cropped")
	crop_size = 1024
	left_margin = 260
	crop_images_in_folder(input_dir, output_dir, crop_size, left_margin)
