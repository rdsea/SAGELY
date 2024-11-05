import cv2
import numpy as np
from cv2.typing import MatLike


# because the nature of the object detection task
# preserving the context and original aspect ratio of the object is the key
def resize_and_pad(image: MatLike, target_size: tuple[int, int, int] = (224, 224, 3)):
    target_height, target_width, dim = target_size

    # Compute the scale factor and resize
    scale = min(target_height / image.shape[0], target_width / image.shape[1])
    new_size = (int(image.shape[1] * scale), int(image.shape[0] * scale))
    resized = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)

    # Compute padding sizes
    pad_vert = (target_height - resized.shape[0]) / 2
    pad_horz = (target_width - resized.shape[1]) / 2
    pad_t = int(np.floor(pad_vert))
    pad_b = int(np.ceil(pad_vert))
    pad_l = int(np.floor(pad_horz))
    pad_r = int(np.ceil(pad_horz))

    # Pad the resized image using cv2.copyMakeBorder
    padded = cv2.copyMakeBorder(
        resized,
        pad_t,
        pad_b,
        pad_l,
        pad_r,
        cv2.BORDER_CONSTANT,
        value=[0, 0, 0],  # Assuming padding with black pixels
    )

    return padded


def resize(image: MatLike, target_size: tuple[int, int] = (224, 224)):
    resized_image = cv2.resize(image, target_size, interpolation=cv2.INTER_AREA)
    return resized_image


# def resize_and_pad(image: MatLike, target_size: tuple[int, int, int] = (32, 32, 3)):
#     target_height, target_width, dim = target_size
#
#     # Compute the scale factor and resize
#     scale = min(target_height / image.shape[0], target_width / image.shape[1])
#     new_size = (int(image.shape[1] * scale), int(image.shape[0] * scale))
#     resized = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
#
#     # Compute padding sizes
#     pad_vert = (target_height - resized.shape[0]) / 2
#     pad_horz = (target_width - resized.shape[1]) / 2
#     pad_t = int(np.floor(pad_vert))
#     pad_b = int(np.ceil(pad_vert))
#     pad_l = int(np.floor(pad_horz))
#     pad_r = int(np.ceil(pad_horz))
#
#     # Pad the resized image
#     padded = np.pad(
#         resized,
#         ((pad_t, pad_b), (pad_l, pad_r), (0, 0)),
#         mode="constant",
#         constant_values=0,
#     )
#
#     return padded


def say_hello():
    print("Hello from image processing functions file")


# can add more image processing function to consider in different situation
