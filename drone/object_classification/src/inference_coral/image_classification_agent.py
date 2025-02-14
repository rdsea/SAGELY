import os
import sys

import cv2
import numpy as np
from pycoral.adapters import classify, common
from pycoral.pybind._pywrap_coral import SetVerbosity as set_verbosity
from pycoral.utils.edgetpu import make_interpreter


from datamodel import (
    ImageClassificationModelEnum,
    ModelConfig,
)

set_verbosity(10)
current_directory = os.path.dirname(os.path.abspath(__file__))
util_directory = os.path.join(current_directory, "..", "util")
sys.path.append(util_directory)

from classes import IMAGENET2012_CLASSES  # noqa: E402

key_list = list(IMAGENET2012_CLASSES.keys())


class ImageClassificationAgent:
    def __init__(
        self,
        chosen_model: ImageClassificationModelEnum,
        model_config: ModelConfig,
    ):
        self.interpreter = make_interpreter(
            f"./tflite_tpu_model/{chosen_model.value}_edgetpu.tflite"
        )
        self.interpreter.allocate_tensors()

        self.size = common.input_size(self.interpreter)
        self.input_details = self.interpreter.get_input_details()

        self.output_details = self.interpreter.get_output_details()
        self.model_config = model_config

        self.params = common.input_details(self.interpreter, "quantization_parameters")
        self.scale = self.params["scales"]
        self.zero_point = self.params["zero_points"]
        self.top_k = 3
        self.threshold = 0.1
        self.std = 128.0
        self.mean = 128.0

    def reshape(self, image_array, enlarge: bool):
        # NOTE: interpolation choice taken from https://stackoverflow.com/questions/23853632/which-kind-of-interpolation-best-for-resizing-image
        reshaped_image = cv2.resize(
            image_array,
            self.model_config.input_shape[1:2],
            interpolation=cv2.INTER_LINEAR if enlarge else cv2.INTER_AREA,
        )
        return reshaped_image

    def predict(self, image_array):
        if image_array.shape[1] != self.model_config.input_shape[1]:
            image_array = self.reshape(
                image_array, image_array.shape[1] > self.model_config.input_shape[1]
            )

        # image_array = preprocess_input(image_array, mode=self.model_config.input_mode)

        if (
            abs(self.scale * self.std - 1) < 1e-5
            and abs(self.mean - self.zero_point) < 1e-5
        ):
            # Input data does not require preprocessing.
            common.set_input(self.interpreter, image_array)
        else:
            # Input data requires preprocessing
            normalized_input = (np.asarray(image_array) - self.mean) / (
                self.std * self.scale
            ) + self.zero_point
            np.clip(normalized_input, 0, 255, out=normalized_input)
            common.set_input(self.interpreter, normalized_input.astype(np.uint8))

        self.interpreter.invoke()
        classes = classify.get_classes(self.interpreter, self.top_k, self.threshold)
        return classes
