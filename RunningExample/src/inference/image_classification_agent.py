import os
import sys
from typing import Optional

import cv2
import numpy as np
import onnxruntime as ort
from numpy._typing import NDArray

from datamodel import ImageClassificationModelEnum, ModelConfig

current_directory = os.path.dirname(os.path.abspath(__file__))
util_directory = os.path.join(current_directory, "..", "util")
sys.path.append(util_directory)

from classes import IMAGENET2012_CLASSES  # noqa: E402
from preprocessing import preprocess_input  # noqa: E402

key_list = list(IMAGENET2012_CLASSES.keys())


class ImageClassificationAgent:
    def __init__(
        self,
        chosen_model: ImageClassificationModelEnum,
        model_config: ModelConfig,
        execution_provider: Optional[str] = None,
    ):
        session_options = ort.SessionOptions()
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        if execution_provider is not None:
            providers.insert(0, execution_provider)
        self.session = ort.InferenceSession(
            f"./onnx_model/{chosen_model.name}.onnx",
            providers=providers,
            sess_options=session_options,
        )
        self.model_config = model_config

        self.input_name = self.session.get_inputs()[0].name

    def reshape(self, image_array: NDArray, enlarge: bool):
        # NOTE: interpolation choice taken from https://stackoverflow.com/questions/23853632/which-kind-of-interpolation-best-for-resizing-image
        reshaped_image = cv2.resize(
            image_array,
            self.model_config.input_shape[1:2],
            interpolation=cv2.INTER_LINEAR if enlarge else cv2.INTER_AREA,
        )
        return reshaped_image

    def predict(self, image_array: NDArray):
        if image_array.shape[1] != self.model_config.input_shape[1]:
            image_array = self.reshape(
                image_array, image_array.shape[1] > self.model_config.input_shape[1]
            )

        print(self.model_config.input_mode)
        image_array = preprocess_input(image_array, mode=self.model_config.input_mode)

        if len(image_array.shape) != 4:
            image_array = np.expand_dims(image_array, axis=0)

        outputs = self.session.run(None, {self.input_name: image_array})
        outputs = outputs[0]

        predicted_class_index = np.argmax(outputs, axis=1)[0]
        return key_list[predicted_class_index], float(outputs[0][predicted_class_index])
