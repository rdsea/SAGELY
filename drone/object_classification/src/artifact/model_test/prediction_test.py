import time

import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.resnet50 import (
    ResNet50,
    decode_predictions,
    preprocess_input,
)

model = ResNet50(weights="imagenet")

img_path = "elephant.jpg"
img = tf.keras.utils.load_img(img_path, target_size=(224, 224))
x = tf.keras.utils.img_to_array(img)
x = np.expand_dims(x, axis=0)
x = preprocess_input(x)

avg_time = 0
for _ in range(10):
    start_time = time.time()
    preds = model.predict(x)
    print("Predicted:", decode_predictions(preds, top=3)[0])
    avg_time += time.time() - start_time

print(avg_time / 10)
