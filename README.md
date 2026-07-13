
# CEI-Dataset Instructions

## 1. Cropping Images

Run the following command to crop all `ms_N.png` and `ms_N_real.png` images into 1024x1024 TIFF tiles (with a 260px left margin):

```sh
.venv/bin/python crop_img.py
```

- Cropped label images will be saved in `data/raw/cropped/label/`.
- Cropped real images will be saved in `data/raw/cropped/real/`.
- Tiles are named `maesuai_1.tif`, `maesuai_2.tif`, etc.
- The script automatically processes all images in `data/raw/Images/`.

Dataset roles:

- `label/`: cropped images used for pretraining and prediction.
- `real/`: cropped real images used for real dataset training.

- To use the older single-folder crop mode, run:

```sh
.venv/bin/python crop_img.py --mode standard --only ms_1.png --output-dir data/raw/cropped/ms_1
```

## 2. Labeling

- There are 195 images to label.
- After labeling, save each GeoJSON file using the following naming convention:
	- For buildings: `b_geojson_0001.geojson`
	- For sports: `s_geojson_0001.geojson`
	- For vegetation: `v_geojson_0001.geojson`
	- For road lines: `rl_geojson_0001.geojson`
	- etc.
- Place each GeoJSON file in its corresponding subdirectory under `data/annotation/` (e.g., `data/annotation/building/`).

- **Labeling guidelines:** Follow the instructions in the [label technique document](https://docs.google.com/document/d/1iKMLfSWxGtZCozzISkt_GM6rlkliU8h-G4-rDuNDHtQ/edit?tab=t.0#heading=h.pmfk1e8gy3rb).

## 3. Combining Annotations

After labeling, run:

```sh
python3 combine_annotation.py
```

- This script combines all category annotations (building, road, sport, vege, water) for each image into a single GeoJSON file per image.
- Output is saved in a combined annotations directory (the script may need to be updated to match your folder structure).

## 4. Generating Mask Images

After combining annotations, run:

```sh
python3 generate_mask.py
```

- This script generates mask images from the combined annotation files.
- Output masks are saved in the appropriate directory (the script may need to be updated to match your folder structure).


## Folder 
![alt text](image.png)
---

**Note:**
- Make sure your directory structure and file naming match what the scripts expect.
- If you need the scripts to match a different folder or naming convention, let me know and I can help update them.
