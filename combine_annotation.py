import json
import os
from pathlib import Path

def combine_annotations():
    """
    Combine all annotation categories (building, road, sport, vege, water) 
    into single geojson files per image.
    """
    # Define paths
    base_path = Path("data-set(b)/annotations")
    output_path = Path("data-set(b)/combined_annotations")
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Define categories and their prefixes
    categories = {
        "building": "b",
        "road": "r",
        "sport": "s",
        "vege": "v",
        "water": "w"
    }
    
    # Get number of images (assuming 10 images numbered 001-010)
    image_numbers = [f"{i:03d}" for i in range(1, 11)]
    
    print(f"Combining annotations for {len(image_numbers)} images...")
    
    for img_num in image_numbers:
        # Initialize combined geojson structure
        combined_geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        # Collect features from all categories
        for category, prefix in categories.items():
            geojson_file = base_path / category / f"{prefix}_{img_num}.geojson"
            
            if geojson_file.exists():
                try:
                    with open(geojson_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Add category information to each feature
                    if "features" in data:
                        for feature in data["features"]:
                            if "properties" not in feature:
                                feature["properties"] = {}
                            feature["properties"]["category"] = category
                            combined_geojson["features"].append(feature)
                    
                    print(f"  ✓ Added {category} annotations for image {img_num}")
                except Exception as e:
                    print(f"  ✗ Error reading {geojson_file}: {e}")
            else:
                print(f"  ⚠ File not found: {geojson_file}")
        
        # Write combined geojson file
        output_file = output_path / f"{img_num}.geojson"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(combined_geojson, f, indent=2, ensure_ascii=False)
            print(f"✓ Created combined file: {output_file} ({len(combined_geojson['features'])} features)\n")
        except Exception as e:
            print(f"✗ Error writing {output_file}: {e}\n")
    
    print(f"Done! Combined annotations saved to: {output_path}")
    print(f"Total files created: {len(list(output_path.glob('*.geojson')))}")


if __name__ == "__main__":
    combine_annotations()
