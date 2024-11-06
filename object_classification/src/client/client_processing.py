import argparse
import os
import random
import sys
import time
from threading import Timer

import requests

current_directory = os.path.dirname(os.path.abspath(__file__))
util_directory = os.path.join(current_directory, "..", "util")
sys.path.append(util_directory)


def send_request(url, requesting_interval, jpeg_images_list):
    timer = Timer(
        requesting_interval,
        send_request,
        args=(
            url,
            requesting_interval,
            jpeg_images_list,
        ),
    )
    timer.start()

    random_image = random.choice(jpeg_images_list)
    image_path = os.path.join(ds_path, random_image)

    # Extract the synset_id from the file name
    root, _ = os.path.splitext(image_path)
    _, synset_id = os.path.basename(root).rsplit("_", 1)

    # Open the image file as binary
    with open(image_path, "rb") as img_file:
        img_data = img_file.read()

    start_time = time.time()
    file = {"file": ("random_image", img_data, "image/jpeg")}
    response = requests.post(url, files=file)
    print(response.json(), synset_id, (time.time() - start_time) * 1000)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Argument for choosingg model to request"
    )
    parser.add_argument(
        "--ds_path",
        type=str,
        help="test dataset path",
        default="../artifact/dataset/imagenet/data/val_images/",
    )
    parser.add_argument(
        "--rate", type=int, help="number of requests per second", default=1
    )
    parser.add_argument(
        "--device_id", type=str, help="specify device id", default="aaltosea_cam_01"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="request url",
        default="http://localhost:5010/preprocessing",
    )

    # Parse the parameters
    args = parser.parse_args()
    device_id = args.device_id
    ds_path = args.ds_path
    req_rate = args.rate
    url = args.url

    files = os.listdir(ds_path)
    jpeg_images_list = [file for file in files if file.lower().endswith(".jpeg")]
    requesting_interval = 1.0 / req_rate
    timer = Timer(
        requesting_interval,
        send_request,
        args=(
            url,
            requesting_interval,
            jpeg_images_list,
        ),
    )
    timer.start()
