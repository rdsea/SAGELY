import os
import shutil

from classes import IMAGENET2012_CLASSES

# Path to the directory containing the images
dir_path = "./data/val_images/"
output_dir = "./data/val_images_splitted"

# Iterate over each file in the directory
for file in os.listdir(dir_path):
    if file.endswith(".JPEG"):
        # Split the filename to extract the synset_id
        root, _ = os.path.splitext(file)
        _, synset_id = os.path.basename(root).rsplit("_", 1)

        # Get the label using the synset_id
        label = IMAGENET2012_CLASSES[synset_id]
        print(file, label)

        # Define the new directory path based on the synset_id
        synset_dir = os.path.join(output_dir, synset_id)

        # Create the directory if it does not exist
        os.makedirs(synset_dir, exist_ok=True)

        # Define the source and destination file paths
        src_file = os.path.join(dir_path, file)
        dst_file = os.path.join(synset_dir, file)

        # Move the file to the new directory
        shutil.move(src_file, dst_file)

print("Images have been sorted into directories based on synset_id.")
