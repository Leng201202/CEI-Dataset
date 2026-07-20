# Total Area

Computed from the existing area CSV files in this repository.

## Full Image Area

| Source CSV | Images | Pixel size | Total pixels | Total area (m2) | Total area (km2) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `data/image_area_google_earth.csv` | 84 | 0.276213587 m | 88,080,384 | 6,720,000.029146 | 6.720000029146 |
| `data/image_area_pixel_1m.csv` | 84 | 1.0 m | 88,080,384 | 88,080,384.000000 | 88.080384 |

Using the Google Earth-derived pixel size, the total full image area is **6.72 km2**.

## Review Mask Foreground Area

| Source CSV | Masks | Pixel size | Foreground pixels | Total area (m2) | Total area (km2) |
| --- | ---: | ---: | ---: | ---: | ---: |
| `data/raw/review_area_sample_pixel_1m.csv` | 84 | 1.0 m | 38,023,529 | 38,023,529.000000 | 38.023529 |

The review mask foreground area assumes 1 m pixels and excludes the dominant background color in each mask.
