# Total Area

Computed from the existing area CSV files in this repository. The area CSVs
currently cover the working set `maesuai_1`-`maesuai_100`; `maesuai_101`-`112`
are held back for now (see note below).

## Full Image Area

The Google Earth pixel size differs per source image. Crops from ms_1-ms_3
(`maesuai_1`-`maesuai_84`) use 0.276213587 m from the original measurement.
Crops from ms_4 use 0.249658624 m, derived from the latest Google Earth
measurement of 1.83 km2 for the full 28-tile ms_4 region (`maesuai_85`-`112`).

| Source CSV | Images | Pixel size | Total pixels | Total area (m2) | Total area (km2) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `data/image_area_google_earth.csv` (maesuai_1-84, from ms_1-ms_3) | 84 | 0.276213587 m | 88,080,384 | 6,720,000.029146 | 6.720000029146 |
| `data/image_area_google_earth.csv` (maesuai_85-100, from ms_4) | 16 | 0.249658624 m | 16,777,216 | 1,045,714.285714 | 1.045714285714 |
| `data/image_area_google_earth.csv` (all) | 100 | mixed | 104,857,600 | 7,765,714.314861 | 7.765714314861 |
| `data/image_area_pixel_1m.csv` | 100 | 1.0 m | 104,857,600 | 104,857,600.000000 | 104.857600 |

Using the Google Earth-derived pixel sizes, the total full image area for
`maesuai_1`-`maesuai_100` is **7.77 km2** (6.72 km2 for ms_1-ms_3 +
1.05 km2 for the ms_4 tiles 85-100).

**Held back:** `maesuai_101`-`112` (12 ms_4 tiles, 12,582,912 px) are not in
the CSVs yet. At the same pixel size they add 784,285.714286 m2 (0.784286 km2),
which brings the ms_4 group to its measured 1.83 km2 and the grand total to
8.55 km2 once included.

## Review Mask Foreground Area

| Source CSV | Masks | Pixel size | Foreground pixels | Total area (m2) | Total area (km2) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `data/raw/review_area_sample_pixel_1m.csv` | 84 | 1.0 m | 38,023,529 | 38,023,529.000000 | 38.023529 |

The review mask foreground area assumes 1 m pixels and excludes the dominant
background color in each mask. This CSV still covers only `maesuai_1`-`maesuai_84`;
the ms_4 masks have not been added to it yet.
