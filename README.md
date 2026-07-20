## CEI Dataset

Land-cover segmentation dataset for CEI aerial imagery (Mae Suai). 112 image /
mask pairs at 1024x1024, 1 m ground resolution.

### Labels

Labels are authored **as RGB colour**. A mask is an ordinary RGB TIFF; a Tree
pixel is literally the bytes `34, 97, 38`. There is no class id, name, or
palette index stored inside the mask files -- the colour *is* the label.

Numeric class ids are assigned later, as a build step, by `rgb_to_class_id.py`.
The mapping lives in `classes.json`, which is the authoritative definition for
both the exporter and any dataloader.

| Id | Class | Colour (RGB) | Covers |
| --- | --- | --- | --- |
| 0 | Unlabeled (ignore) | 0, 0, 0 | Cannot be determined |
| 1 | Rangeland | 0, 255, 36 | Grass, shrubs, parks, golf courses, uncultivated vegetation |
| 2 | Agriculture | 75, 181, 73 | Farmland, agriculture land |
| 3 | Tree | 34, 97, 38 | A tree, forest |
| 4 | Water | 0, 69, 255 | Rivers, lakes, ponds, dams, sea, swimming pools |
| 5 | Building | 222, 31, 7 | Building |
| 6 | Road | 255, 255, 255 | Surface designed for vehicular movement |
| 7 | Non-Vegetated | 128, 0, 0 | Sport, bareland, pavement, sidewalk, parking lots, sand, rocks, exposed soil, non-vegetated natural surface |

Id 0 is reserved as `ignore_index` and is currently **unused** -- no mask
contains black pixels. Train with `num_classes=8` and `ignore_index=0`.

"Developed space" (148, 148, 148) was a class in earlier revisions. It has been
merged into Non-Vegetated across all 112 masks and must not be painted.

### Workflow

Labelling and id assignment are deliberately separate, so the labelling team
never has to think about ids.

1. **Label.** Correct the draft masks in GIMP using `oem_palette.gpl`. See
   `data/raw/review/HOW_TO_EDIT.md`. The `.tif` masks are the deliverable and
   the source of truth.
2. **Convert.** Once labelling is done, export class-id masks:

       python rgb_to_class_id.py --check     # validate colours, writes nothing
       python rgb_to_class_id.py --stats     # write data/masks/, print balance

`data/masks/` is generated output -- safe to delete and rebuild. The `.tif`
masks are never modified.

### Checking for mis-colouring

Because the colour is the label, a wrong colour is a wrong label. The usual
cause is painting with the Paintbrush instead of the Pencil: anti-aliasing
invents blended colours like `35, 98, 39`, which is not Tree and not any other
class.

`--check` validates every pixel against the palette and reports what is wrong:

    python rgb_to_class_id.py --check                                  # whole folder
    python rgb_to_class_id.py --check --input path/to/one_mask.tif     # single file

    FAIL dirty_mask.tif: 245 off-palette px in 3 colour(s)
           (35, 98, 39)       x200      nearest: Tree (anti-aliased edge)
           (200, 10, 90)      x5        nearest: Building, but not close -- check this one

Nearest-class output is advisory only; nothing is ever snapped to it. A file
with off-palette pixels is skipped rather than written, and the run exits 1, so
bad colours cannot silently reach training. Teammates can run `--check` on their
own file as they go rather than waiting for the final conversion.

As of the current revision all 112 masks pass with zero off-palette pixels.

### Class balance

Measured over all 112 masks. Note the imbalance -- Tree is roughly 17x Road,
which is worth accounting for in the loss.

| Class | Share |
| --- | --- |
| Tree | 43.18% |
| Agriculture | 26.49% |
| Rangeland | 12.58% |
| Non-Vegetated | 6.93% |
| Water | 5.05% |
| Building | 3.22% |
| Road | 2.56% |

### Adjusting classes later

- **Change an id** -- edit `classes.json`, re-run the exporter. Masks untouched.
- **Change a colour** -- edit `classes.json` *and* recolour the existing masks.
  Both halves are required; otherwise `--check` will correctly reject the old
  colour as off-palette.
- **Add or remove a class** -- this changes the label space the model learns.

### Directory structure

    classes.json              class id <-> colour <-> name (authoritative)
    rgb_to_class_id.py        RGB masks -> single-channel class-id masks
    calculate_area.py         mask area statistics in px / m2 / km2
    crop_img.py               tiling of source imagery
    data/images/              cropped aerial images (112)
    data/masks/               generated class-id labels (not yet built)
    data/raw/review/          RGB masks + GIMP palette + labelling guide
    data/raw/Images/          full-resolution source imagery
    data/raw/output/          model predictions

### Citation

If you use this dataset in a project or publication, add the recommended
citation here.

### License

Add license information here.
