import argparse
import csv
import os
import time

import numpy as np
import onnxruntime as ort
from classes import IMAGENET2012_CLASSES
from PIL import Image
from preprocessing import preprocess_input
from tqdm import tqdm

MODEL_CONFIG = {
    "DenseNet121": [(1, 224, 224, 3), "torch"],
    "DenseNet201": [(1, 224, 224, 3), "torch"],
    "EfficientNetB0": [(1, 224, 224, 3), "raw"],
    "EfficientNetB7": [(1, 600, 600, 3), "raw"],
    "EfficientNetV2L": [(1, 480, 480, 3), "raw"],
    "EfficientNetV2S": [(1, 384, 384, 3), "raw"],
    "InceptionResNetV2": [(1, 299, 299, 3), "tf"],
    "InceptionV3": [(1, 299, 299, 3), "tf"],
    "MobileNet": [(1, 224, 224, 3), "tf"],
    "MobileNetV2": [(1, 224, 224, 3), "tf"],
    "NASNetLarge": [(1, 331, 331, 3), "tf"],
    "NASNetMobile": [(1, 224, 224, 3), "tf"],
    "ResNet50": [(1, 224, 224, 3), "caffe"],
    "ResNet50V2": [(1, 224, 224, 3), "tf"],
    "VGG16": [(1, 224, 224, 3), "caffe"],
    "Xception": [(1, 299, 299, 3), "tf"],
}


def load_model(model_path):
    session_options = ort.SessionOptions()
    session = ort.InferenceSession(
        model_path,
        providers=["CUDAExecutionProvider"],
        sess_options=session_options,
    )

    return session


def preprocess_image(image_path, input_shape, input_mode):
    image = Image.open(image_path).convert("RGB")
    image = image.resize((input_shape[1], input_shape[2]))
    # NOTE: careful, the range is different for each models
    image_array = np.array(image).astype("float32")
    image_array = preprocess_input(image_array, mode=input_mode)

    image_array = np.expand_dims(image_array, axis=0)
    return image_array


def get_predictions(model, image_array, input_name):
    start_time = time.time()
    outputs = model.run(None, {input_name: image_array})
    return outputs[0], (time.time() - start_time) * 1000


def evaluate_model(model_name, model, image_dir, input_shape, input_mode: str):
    key_list = list(IMAGENET2012_CLASSES.keys())
    input_name = model.get_inputs()[0].name
    images_list = os.listdir(image_dir)[:1000]
    images_list.sort()

    data = []

    for file in tqdm(images_list):
        if file.endswith(".JPEG"):
            root, _ = os.path.splitext(file)
            _, synset_id = os.path.basename(root).rsplit("_", 1)

            image_path = os.path.join(image_dir, file)
            image_array = preprocess_image(image_path, input_shape, input_mode)
            output, latency = get_predictions(model, image_array, input_name)
            predicted_class = np.argmax(output, axis=1)[0]

            key_at_index = key_list[predicted_class]

            data.append([file, synset_id, key_at_index, latency])

    csv_file_path = f"./results/{model_name}.csv"
    with open(csv_file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Filename", "Ground Truth", "Prediction", "Latency (ms)"])
        writer.writerows(data)
    print(f"Finish profiling {model_name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", help="model name", default="MobileNet")
    args = parser.parse_args()

    model_name = args.model
    model_path = f"./{model_name}.onnx"
    image_dir = "./data"

    base_model = model_name.split("_")[0]
    input_shape = MODEL_CONFIG[base_model][0]
    input_mode = MODEL_CONFIG[base_model][1]

    model = load_model(model_path)

    evaluate_model(model_name, model, image_dir, input_shape, input_mode)
