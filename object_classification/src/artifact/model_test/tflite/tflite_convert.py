import os

import tensorflow as tf

# Convert the model
path = "./model/"
dir_list = os.listdir(path)
for dir in dir_list:
    saved_model_path = path + dir
    converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_path)
    tflite_model = converter.convert()
    with open(f"{dir}.tflite", "wb") as f:
        f.write(tflite_model)
    print(f"done writing model {dir}")
