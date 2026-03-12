import json
import numpy as np
import cv2
from pathlib import Path
from tqdm import tqdm

TILE_SIZE = 1024
BACKGROUND_VALUE = 0   # black background

# Define pixel values for each category
CATEGORY_VALUES = {
    "building": 51,
    "road": 102,
    "sport": 153,
    "vege": 204,
    "water": 255
}

# Legacy value for backward compatibility
BUILDING_VALUE = 123   # grey building

annotations_dir = Path("data-set(b)/annotations")
masks_dir = Path("data-set(b)/masks")
combined_annotations_dir = Path("data-set(b)/combined_annotations")
combined_masks_dir = Path("data-set(b)/combined_masks")

def flip_y_if_negative(coords):
    new_coords = []
    for x, y in coords:
        # Convert negative Y coordinates to positive (flip vertically)
        new_coords.append([x, abs(y)])
    return new_coords

def generate_combined_masks():
    """Generate masks from combined annotations with all categories."""
    print("\n=== Processing Combined Annotations ===")
    
    if not combined_annotations_dir.exists():
        print(f"Combined annotations directory not found: {combined_annotations_dir}")
        return
    
    combined_masks_dir.mkdir(parents=True, exist_ok=True)
    
    geojson_files = list(combined_annotations_dir.glob("*.geojson"))
    
    for geojson_file in tqdm(geojson_files, desc="Combined masks"):
        with open(geojson_file) as f:
            data = json.load(f)
        
        mask = np.full((TILE_SIZE, TILE_SIZE), BACKGROUND_VALUE, dtype=np.uint8)
        
        for feature in data["features"]:
            geom = feature["geometry"]
            
            if geom["type"] != "Polygon":
                continue
            
            # Get category from feature properties
            category = feature.get("properties", {}).get("category", "building")
            pixel_value = CATEGORY_VALUES.get(category, BUILDING_VALUE)
            
            polygon = geom["coordinates"][0]
            polygon = flip_y_if_negative(polygon)
            
            pts = np.array(polygon, np.int32)
            pts = pts.reshape((-1, 1, 2))
            
            cv2.fillPoly(mask, [pts], pixel_value)
        
        out_path = combined_masks_dir / (geojson_file.stem + ".png")
        cv2.imwrite(str(out_path), mask)
    
    print(f"✓ Generated {len(geojson_files)} combined masks in {combined_masks_dir}")

def generate_individual_masks():
    """Generate masks from individual category annotations (original structure)."""
    print("\n=== Processing Individual Category Annotations ===")
    
    geojson_files = list(annotations_dir.glob("**/*.geojson"))
    
    for geojson_file in tqdm(geojson_files, desc="Individual masks"):
        with open(geojson_file) as f:
            data = json.load(f)

        mask = np.full((TILE_SIZE, TILE_SIZE), BACKGROUND_VALUE, dtype=np.uint8)

        for feature in data["features"]:
            geom = feature["geometry"]

            if geom["type"] != "Polygon":
                continue

            polygon = geom["coordinates"][0]
            polygon = flip_y_if_negative(polygon)

            pts = np.array(polygon, np.int32)
            pts = pts.reshape((-1, 1, 2))

            cv2.fillPoly(mask, [pts], BUILDING_VALUE)

        # Preserve subdirectory structure in masks
        relative_path = geojson_file.relative_to(annotations_dir)
        out_path = masks_dir / relative_path.parent / (geojson_file.stem + ".png")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out_path), mask)
    
    print(f"✓ Generated {len(geojson_files)} individual masks in {masks_dir}")

if __name__ == "__main__":
    # Generate masks from individual category folders
    generate_individual_masks()
    
    # Generate masks from combined annotations
    generate_combined_masks()
    
    print("\n" + "="*50)
    print("Mask generation complete!")
    print(f"Individual masks: {masks_dir}")
    print(f"Combined masks: {combined_masks_dir}")
    print("\nCategory pixel values:")
    for category, value in CATEGORY_VALUES.items():
        print(f"  {category}: {value}")
    print("="*50)