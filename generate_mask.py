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
    "roadline": 102,
    "roadarea": 102,
    "sport": 153,
    "vege": 204,
    "water": 255
}

# Legacy value for backward compatibility
BUILDING_VALUE = 123   # grey building

annotations_dir = Path("data/annotation")
masks_dir = Path("data/masks")
combined_annotations_dir = Path("data/combined_annotations")
combined_masks_dir = Path("data/combined_masks")

def flip_y_if_negative(coords):
    new_coords = []
    for x, y in coords:
        # Convert negative Y coordinates to positive (flip vertically)
        # Assuming the coordinate system is such that negative Y values need flipping
        new_coords.append([x, abs(y)])
    return new_coords

def generate_combined_masks():
    """Generate masks from combined annotations with all categories."""
    print("\n=== Processing Combined Annotations ===")
    
    if not combined_annotations_dir.exists():
        print(f"Combined annotations directory not found: {combined_annotations_dir}")
        return
    
    combined_masks_dir.mkdir(parents=True, exist_ok=True)
    
    geojson_files = sorted(list(combined_annotations_dir.glob("*.geojson")))
    
    for geojson_file in tqdm(geojson_files, desc="Combined masks"):
        with open(geojson_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        mask = np.full((TILE_SIZE, TILE_SIZE), BACKGROUND_VALUE, dtype=np.uint8)
        
        for feature in data.get("features", []):
            geom = feature.get("geometry")
            if not geom or "coordinates" not in geom:
                continue
            
            # Get category from feature properties
            category = feature.get("properties", {}).get("category", "")
            pixel_value = CATEGORY_VALUES.get(category, 0)
            if pixel_value == 0:
                continue

            if geom["type"] == "Polygon" and geom["coordinates"]:
                polygon = geom["coordinates"][0]
                if not polygon:
                    continue
                polygon = flip_y_if_negative(polygon)
                
                pts = np.array(polygon, np.int32)
                if pts.size == 0:
                    continue
                pts = pts.reshape((-1, 1, 2))
                cv2.fillPoly(mask, [pts], int(pixel_value))
                
            elif geom["type"] == "LineString" and geom["coordinates"]:
                line = geom["coordinates"]
                if not line:
                    continue
                line = flip_y_if_negative(line)
                
                pts = np.array(line, np.int32)
                if pts.size == 0:
                    continue
                pts = pts.reshape((-1, 1, 2))
                # Draw line with thickness (e.g., 6 pixels)
                cv2.polylines(mask, [pts], isClosed=False, color=int(pixel_value), thickness=6)
        
        out_path = combined_masks_dir / (geojson_file.stem + ".png")
        cv2.imwrite(str(out_path), mask)
    
    print(f"✓ Generated {len(geojson_files)} combined masks in {combined_masks_dir}")

def generate_individual_masks():
    """Generate masks from individual category annotations (original structure)."""
    print("\n=== Processing Individual Category Annotations ===")
    
    if not annotations_dir.exists():
        print(f"Individual annotations directory not found: {annotations_dir}")
        return

    geojson_files = sorted(list(annotations_dir.glob("**/*.geojson")))
    
    for geojson_file in tqdm(geojson_files, desc="Individual masks"):
        with open(geojson_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        mask = np.full((TILE_SIZE, TILE_SIZE), BACKGROUND_VALUE, dtype=np.uint8)

        # Determine default pixel value based on directory name
        category = geojson_file.parent.name
        pixel_value = CATEGORY_VALUES.get(category, BUILDING_VALUE)

        for feature in data.get("features", []):
            geom = feature.get("geometry")
            if not geom or "coordinates" not in geom:
                continue

            if geom["type"] == "Polygon" and geom["coordinates"]:
                polygon = geom["coordinates"][0]
                if not polygon:
                    continue
                polygon = flip_y_if_negative(polygon)

                pts = np.array(polygon, np.int32)
                if pts.size == 0:
                    continue
                pts = pts.reshape((-1, 1, 2))
                cv2.fillPoly(mask, [pts], int(pixel_value))
            
            elif geom["type"] == "LineString" and geom["coordinates"]:
                line = geom["coordinates"]
                if not line:
                    continue
                line = flip_y_if_negative(line)
                
                pts = np.array(line, np.int32)
                if pts.size == 0:
                    continue
                pts = pts.reshape((-1, 1, 2))
                cv2.polylines(mask, [pts], isClosed=False, color=int(pixel_value), thickness=6)

        # Preserve subdirectory structure in masks
        try:
            relative_path = geojson_file.relative_to(annotations_dir)
            out_path = masks_dir / relative_path.parent / (geojson_file.stem + ".png")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(out_path), mask)
        except Exception as e:
            print(f"  ✗ Error saving mask for {geojson_file}: {e}")
    
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