import os
import sys

import tflite_runtime.interpreter as tflite
from fastapi import FastAPI, UploadFile

# Set up the utility directory path
current_directory = os.path.dirname(os.path.abspath(__file__))
util_directory = os.path.join(current_directory, "../../..", "util")
sys.path.append(util_directory)

from load_image import img_to_array, load_img  # noqa: E402

app = FastAPI()


interpreter = tflite.Interpreter(model_path="./tflite_model/MobileNet.tflite")
interpreter.allocate_tensors()

# Get input and output tensors
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

input_shape = input_details[0]["shape"]
size = input_shape[1]


@app.post("/predict")
async def predict(file: UploadFile):
    # Read the uploaded file
    file_data = await file.read()

    image = load_img(file_data, target_size=(size, size))

    input_data = img_to_array(image, dtype=input_details[0]["dtype"])

    interpreter.set_tensor(input_details[0]["index"], input_data)
    interpreter.invoke()

    _ = interpreter.get_tensor(output_details[0]["index"])

    return "Ok"
