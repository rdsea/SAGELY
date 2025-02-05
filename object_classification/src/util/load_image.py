"""
Taken from https://github.com/keras-team/keras/blob/v3.3.3/keras/src/utils/image_utils.py#L187-L293
"""

import io
import pathlib
from typing import Union

import numpy as np
from PIL import Image
from PIL.ImageFile import ImageFile

PIL_INTERPOLATION_METHODS = {
    "nearest": Image.Resampling.NEAREST,
    "bilinear": Image.Resampling.BILINEAR,
    "bicubic": Image.Resampling.BICUBIC,
    "hamming": Image.Resampling.HAMMING,
    "box": Image.Resampling.BOX,
    "lanczos": Image.Resampling.LANCZOS,
}


def load_img(
    path: Union[pathlib.Path, bytes, str, io.BytesIO],
    color_mode="rgb",
    target_size=None,
    interpolation="nearest",
    keep_aspect_ratio=False,
):
    if isinstance(path, io.BytesIO):
        img = Image.open(path)
    elif isinstance(path, pathlib.Path):
        path = str(path.resolve())
    if isinstance(path, bytes):
        img = Image.open(io.BytesIO(path))
    elif isinstance(path, str):
        with open(path, "rb") as f:
            img = Image.open(io.BytesIO(f.read()))
    else:
        raise TypeError(f"path should be path-like or io.BytesIO, not {type(path)}")

    if color_mode == "grayscale":
        # if image is not already an 8-bit, 16-bit or 32-bit grayscale image
        # convert it to an 8-bit grayscale image.
        if img.mode not in ("L", "I;16", "I"):
            img = img.convert("L")
    elif color_mode == "rgba":
        if img.mode != "RGBA":
            img = img.convert("RGBA")
    elif color_mode == "rgb":
        if img.mode != "RGB":
            img = img.convert("RGB")
    else:
        raise ValueError('color_mode must be "grayscale", "rgb", or "rgba"')
    if target_size is not None:
        width_height_tuple = (target_size[1], target_size[0])
        if img.size != width_height_tuple:
            if interpolation not in PIL_INTERPOLATION_METHODS:
                raise ValueError(
                    "Invalid interpolation method {} specified. Supported "
                    "methods are {}".format(
                        interpolation,
                        ", ".join(PIL_INTERPOLATION_METHODS.keys()),
                    )
                )
            resample = PIL_INTERPOLATION_METHODS[interpolation]

            if keep_aspect_ratio:
                width, height = img.size
                target_width, target_height = width_height_tuple

                crop_height = (width * target_height) // target_width
                crop_width = (height * target_width) // target_height

                # Set back to input height / width
                # if crop_height / crop_width is not smaller.
                crop_height = min(height, crop_height)
                crop_width = min(width, crop_width)

                crop_box_hstart = (height - crop_height) // 2
                crop_box_wstart = (width - crop_width) // 2
                crop_box_wend = crop_box_wstart + crop_width
                crop_box_hend = crop_box_hstart + crop_height
                crop_box = [
                    crop_box_wstart,
                    crop_box_hstart,
                    crop_box_wend,
                    crop_box_hend,
                ]
                img = img.resize(width_height_tuple, resample, box=crop_box)
            else:
                img = img.resize(width_height_tuple, resample)
    return img


def img_to_array(img: ImageFile, dtype=None):
    """Converts a PIL Image instance to a NumPy array.

    Example:

    ```python
    from PIL import Image
    img_data = np.random.random(size=(100, 100, 3))
    img = keras.utils.array_to_img(img_data)
    array = keras.utils.image.img_to_array(img)
    ```

    Args:
        img: Input PIL Image instance.
        dtype: Dtype to use. `None` means the global setting
            `keras.backend.floatx()` is used (unless you changed it, it
            defaults to `"float32"`).

    Returns:
        A 3D NumPy array.
    """

    if dtype is None:
        dtype = np.float32
    # NumPy array x has format (height, width, channel)
    # or (channel, height, width)
    # but original PIL image has format (width, height, channel)
    x = np.asarray(img, dtype=dtype)
    if len(x.shape) == 3:
        pass
    elif len(x.shape) == 2:
        x = x.reshape((x.shape[0], x.shape[1], 1))
    else:
        raise ValueError(f"Unsupported image shape: {x.shape}")

    x = np.expand_dims(x, axis=0)
    return x
