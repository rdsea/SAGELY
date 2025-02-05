import tensorflow as tf
import tf2onnx

model = tf.keras.applications.DenseNet121(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/DenseNet121.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"DenseNet121 model converted to {output_path}")

model = tf.keras.applications.DenseNet201(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/DenseNet201.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"DenseNet201 model converted to {output_path}")

model = tf.keras.applications.EfficientNetB0(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/EfficientNetB0.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"EfficientNetB0 model converted to {output_path}")

model = tf.keras.applications.EfficientNetB7(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/EfficientNetB7.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"EfficientNetB7 model converted to {output_path}")

model = tf.keras.applications.EfficientNetV2L(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
    include_preprocessing=True,
)

spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/EfficientNetV2L.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"EfficientNetV2L model converted to {output_path}")

model = tf.keras.applications.EfficientNetV2S(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
    include_preprocessing=True,
)

spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/EfficientNetV2S.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"EfficientNetV2S model converted to {output_path}")

model = tf.keras.applications.InceptionResNetV2(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/InceptionResNetV2.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"InceptionResNetV2 model converted to {output_path}")

model = tf.keras.applications.InceptionV3(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/InceptionV3.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"InceptionV3 model converted to {output_path}")

model = tf.keras.applications.MobileNet(
    input_shape=None,
    alpha=1.0,
    depth_multiplier=1,
    dropout=0.001,
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/MobileNet.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"MobileNet model converted to {output_path}")

model = tf.keras.applications.MobileNetV2(
    input_shape=None,
    alpha=1.0,
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/MobileNetV2.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"MobileNetV2 model converted to {output_path}")

model = tf.keras.applications.NASNetLarge(
    input_shape=None,
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/NASNetLarge.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"NASNetLarge model converted to {output_path}")

model = tf.keras.applications.NASNetMobile(
    input_shape=None,
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/NASNetMobile.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"NASNetMobile model converted to {output_path}")

model = tf.keras.applications.ResNet50(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/ResNet50.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"ResNet50 model converted to {output_path}")

model = tf.keras.applications.ResNet50V2(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/ResNet50V2.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"ResNet50V2 model converted to {output_path}")

model = tf.keras.applications.VGG16(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)
spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/VGG16.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"VGG16 model converted to {output_path}")

model = tf.keras.applications.Xception(
    include_top=True,
    weights="imagenet",
    input_tensor=None,
    input_shape=None,
    pooling=None,
    classes=1000,
    classifier_activation="softmax",
)

spec = (tf.TensorSpec((None, *model.input_shape[1:]), tf.float32, name="input"),)
output_path = "./onnx_model/Xception.onnx"
model_proto, _ = tf2onnx.convert.from_keras(
    model, input_signature=spec, opset=13, output_path=output_path
)
print(f"Xception model converted to {output_path}")
