import argparse
import os
import random
import time
import asyncio
import aiohttp
from aiohttp.client_exceptions import ClientError


async def send_request(url, jpeg_images_list, requesting_interval):
    while True:
        try:
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


async def main():
    parser = argparse.ArgumentParser(
        description="Argument for choosing model to request"
    )
    parser.add_argument(
        "--ds_path",
        type=str,
        help="Test dataset path",
        default="./image/",
    )
    parser.add_argument(
        "--rate", type=int, help="Number of requests per second", default=1
    )
    parser.add_argument(
        "--device_id", type=str, help="Specify device ID", default="aaltosea_cam_01"
    )
    parser.add_argument(
        "--url",
        type=str,
        help="request url",
        #default="http://localhost:5010/preprocessing",
        default="http://192.168.49.2:32052/preprocess",# with istio working
        #default="http://localhost:32052/preprocess",# with istio working
    )

    args = parser.parse_args()
    global ds_path
    ds_path = args.ds_path
    req_rate = args.rate
    url = args.url

    files = os.listdir(ds_path)
    jpeg_images_list = [file for file in files if file.lower().endswith(".jpeg")]
    requesting_interval = 1.0 / req_rate

    await send_request(url, jpeg_images_list, requesting_interval)


if __name__ == "__main__":
    asyncio.run(main())
