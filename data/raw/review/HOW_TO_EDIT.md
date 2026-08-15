# How to correct a predicted mask in GIMP

Each image here comes as a pair:

* `<stem>_image.png` -- the CEI aerial image. Reference only; never edit it.
* `<stem>_mask.tif`  -- the model's draft label. **This is the file you edit.**

To generate browser-viewable review images with the satellite on the left and
the mask on the right, run this from the repository root:

    python tif_to_png.py

The combined files are written to `data/raw/review_preview/` as
`<stem>_review.png`. The source images and TIFF masks are not changed.

## One-time setup

1. Open GIMP.
2. Load the class colors: **Windows > Dockable Dialogs > Palettes**, right-click
   in the list, **Import Palette...**, choose *Palette file*, and select
   `oem_palette.gpl` from this folder. You now have the 8 class colors plus
   "Unlabeled (ignore)" and can click one to make it the foreground color.
3. Pick the **Pencil** tool (`N`),  Paintbrush. The pencil has hard edges.
   The paintbrush anti-aliases, which invents blended colors that are not real
   classes. (Those get snapped back to the nearest class on import, so nothing
   breaks -- but the boundary ends up a pixel or two off from what you drew.)

## Editing one mask

1. **File > Open** -> `<stem>_mask.tif`.
2. **File > Open as Layers** -> `<stem>_image.png`. The aerial image lands on top.
3. In the **Layers** panel, drag the image layer **below** the mask layer, then
   lower the *mask* layer's **Opacity** to about 60%. You can now see the aerial
   image through the mask and spot where the model got it wrong.
4. Select the mask layer, pick a class color from the palette, and paint the
   corrections with the Pencil. Zoom in (`+`) for boundaries.
5. Set the mask layer's Opacity back to 100%.
6. **File > Export As...**, keep the name `<stem>_mask.tif`, and overwrite.
   In the TIFF export dialog, LZW compression is fine. Do **not** "Save As" an
   `.xcf` and stop there -- the import step reads the `.tif`.

## Class colors

Import `oem_palette.gpl` in GIMP and paint with these 7 classes plus
"Unlabeled". These are the *only* colors allowed in a mask.

| Class | Color (RGB) | Covers |
| --- | --- | --- |
| Rangeland | 0, 255, 36 | Grass, shrubs, parks, golf courses, uncultivated vegetation |
| Agriculture land | 75, 181, 73 | Farmland, agriculture land |
| Tree | 34, 97, 38 | A tree, forest |
| Water | 0, 69, 255 | Rivers, lakes, ponds, dams, sea, swimming pools |
| Building | 222, 31, 7 | Building |
| Road | 255, 255, 255 | Surface designed for vehicular movement |
| Non-Vegetated | 128, 0, 0 | Sport surfaces, bareland, pavement, sidewalk, parking lots, sand, rocks, exposed soil, non-vegetated natural surface |
| Unlabeled (ignore) | 0, 0, 0 | Cannot be determined |

"Developed space" (148, 148, 148) is **no longer a class**. It was merged into
Non-Vegetated. Do not paint with it.

Paint a region black ("Unlabeled") when you genuinely cannot tell what it is.
Those pixels are excluded from the loss instead of teaching the model a guess.

## When you are done

Nothing further -- the `.tif` masks are the deliverable. Keep painting in these
colors and hand them in.

Numeric class ids get assigned later, in one pass over the finished dataset, by
`rgb_to_class_id.py` at the repo root (mapping in `classes.json`). You do not
need to run it while labelling. It never modifies the `.tif` masks; it only
reads them and writes separate files.
