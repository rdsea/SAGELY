import os
import time

import numpy as np
import tflite_runtime.interpreter as tflite

path = "./tflite_model/"
dir_list = os.listdir(path)

dir_list.sort()
N = 10
for dir in dir_list:
    saved_model_path = path + dir
    interpreter = tflite.Interpreter(model_path=saved_model_path)

    interpreter.allocate_tensors()

    # Get input and output tensors.
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    input_shape = input_details[0]["shape"]
    avg_time = 0
    for _ in range(N):
        input_data = np.array(np.random.random_sample(input_shape), dtype=np.float32)
        start_time = time.time()
        interpreter.set_tensor(input_details[0]["index"], input_data)

        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]["index"])
        avg_time += time.time() - start_time

    print(f"{dir} runtime: {(avg_time / N) * 1000}ms")
