import shutil
import os

# Annotation copy
ann_src = r'C:/Users/SE/Desktop/DL for CEI/CEI-Dataset/data/annotation'
ann_dst = r'C:/Users/SE/Desktop/DL IRSA Project/CEI-dataset/data/annotation'
os.makedirs(ann_dst, exist_ok=True)

def copytree_skip_existing(src, dst):
    for root, dirs, files in os.walk(src):
        rel_path = os.path.relpath(root, src)
        dst_dir = os.path.join(dst, rel_path)
        os.makedirs(dst_dir, exist_ok=True)
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst_dir, file)
            if not os.path.exists(dst_file):
                shutil.copy2(src_file, dst_file)

copytree_skip_existing(ann_src, ann_dst)
print('Annotation files copied (skipping existing).')

# Cropped images copy
img_src = r'C:/Users/SE/Desktop/DL for CEI/CEI-Dataset/data/raw/cropped'
img_dst = r'C:/Users/SE/Desktop/DL for CEI/DL_IRSA_Project/CEI-dataset/data/images'
os.makedirs(img_dst, exist_ok=True)

def copy_images_skip_existing(src, dst):
    for file in os.listdir(src):
        if file.endswith('.aux.xml'):
            continue
        src_file = os.path.join(src, file)
        dst_file = os.path.join(dst, file)
        if os.path.isfile(src_file) and not os.path.exists(dst_file):
            shutil.copy2(src_file, dst_file)

copy_images_skip_existing(img_src, img_dst)
print('Cropped images copied (skipping existing, no .aux.xml files).')
