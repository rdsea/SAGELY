from locust import HttpUser, task, between
import os
import random
import base64

USERNAME = "0"
GROUP_ID = "0"
CREDENTIALS = f"{USERNAME}:{GROUP_ID}"
ENCODED_CREDENTIALS = base64.b64encode(CREDENTIALS.encode()).decode()

HEADERS = {
    "Host": "object-classification.test.com",
    "Authorization": f"Basic {ENCODED_CREDENTIALS}",
}

DS_PATH = "./image/"
JPEG_IMAGES_LIST = [
    file for file in os.listdir(DS_PATH) if file.lower().endswith(".jpeg")
]


def get_random_image():
    random_image = random.choice(JPEG_IMAGES_LIST)
    image_path = os.path.join(DS_PATH, random_image)
    root, _ = os.path.splitext(image_path)
    _, synset_id = os.path.basename(root).rsplit("_", 1)
    return image_path, synset_id


class ImageUploadUser(HttpUser):
    wait_time = between(1, 2)  # Random wait time between requests

    @task
    def upload_image(self):
        try:
            image_path, synset_id = get_random_image()
            with open(image_path, "rb") as img_file:
                img_data = img_file.read()

            files = {"file": ("random_image.jpeg", img_data, "image/jpeg")}
            response = self.client.post("/preprocessing", files=files, headers=HEADERS)

            if response.status_code == 200:
                print(response.json(), synset_id)
            else:
                print(f"Request failed with status {response.status_code}")
        except Exception as e:
            print(f"Error occurred: {e}")
