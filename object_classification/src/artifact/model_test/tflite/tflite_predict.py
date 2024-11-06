import os
import sys

import tflite_runtime.interpreter as tflite

current_directory = os.path.dirname(os.path.abspath(__file__))
util_directory = os.path.join(current_directory, "..", "util")
sys.path.append(util_directory)

from load_image import img_to_array, load_img  # noqa: E402

path = "./tflite_model/"
dir_list = os.listdir(path)
dir_list.sort()

for dir in dir_list:
    saved_model_path = path + dir
    interpreter = tflite.Interpreter(model_path=saved_model_path)

    interpreter.allocate_tensors()

    # Get input and output tensors.
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_shape = input_details[0]["shape"]
    size = input_shape[1]
    image = load_img("./elephant.jpg", target_size=(size, size))
    input_data = img_to_array(image, dtype=input_details[0]["dtype"])
    avg_time = 0

    interpreter.set_tensor(input_details[0]["index"], input_data)

    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]["index"])
