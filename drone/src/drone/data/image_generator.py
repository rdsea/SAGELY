import os
import random
from pathlib import Path

from drone.data.base_data_generator import BaseDataGenerator


class ImageDataGenerator(BaseDataGenerator[bytes]):
    def __init__(self, image_folder: Path | str) -> None:
        """
        Currently only support jpeg image folder
        """
        super().__init__()
        if isinstance(image_folder, str):
            self.image_folder = Path(image_folder)
            if not self.image_folder.exists():
                raise FileNotFoundError(f"Path {image_folder} doesn't exist")
        else:
            self.image_folder = image_folder

        files = os.listdir(self.image_folder)
        self.jpeg_images_list = [
            file for file in files if file.lower().endswith(".jpeg")
        ]

    def next(self):
        random_image = random.choice(self.jpeg_images_list)
        image_path = os.path.join(self.image_folder, random_image)
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()
        return img_data
