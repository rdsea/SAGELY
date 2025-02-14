import os

import onnxruntime as rt

models = [
    (
        "./onnx_model/DenseNet121.onnx",
        "./onnx_graph_optimized_model/DenseNet121_optimized.onnx",
    ),
    (
        "./onnx_model/DenseNet201.onnx",
        "./onnx_graph_optimized_model/DenseNet201_optimized.onnx",
    ),
    (
        "./onnx_model/EfficientNetB0.onnx",
        "./onnx_graph_optimized_model/EfficientNetB0_optimized.onnx",
    ),
    (
        "./onnx_model/EfficientNetB7.onnx",
        "./onnx_graph_optimized_model/EfficientNetB7_optimized.onnx",
    ),
    (
        "./onnx_model/EfficientNetV2L.onnx",
        "./onnx_graph_optimized_model/EfficientNetV2L_optimized.onnx",
    ),
    (
        "./onnx_model/EfficientNetV2S.onnx",
        "./onnx_graph_optimized_model/EfficientNetV2S_optimized.onnx",
    ),
    (
        "./onnx_model/InceptionResNetV2.onnx",
        "./onnx_graph_optimized_model/InceptionResNetV2_optimized.onnx",
    ),
    (
        "./onnx_model/InceptionV3.onnx",
        "./onnx_graph_optimized_model/InceptionV3_optimized.onnx",
    ),
    (
        "./onnx_model/MobileNet.onnx",
        "./onnx_graph_optimized_model/MobileNet_optimized.onnx",
    ),
    (
        "./onnx_model/MobileNetV2.onnx",
        "./onnx_graph_optimized_model/MobileNetV2_optimized.onnx",
    ),
    (
        "./onnx_model/NASNetLarge.onnx",
        "./onnx_graph_optimized_model/NASNetLarge_optimized.onnx",
    ),
    (
        "./onnx_model/NASNetMobile.onnx",
        "./onnx_graph_optimized_model/NASNetMobile_optimized.onnx",
    ),
    (
        "./onnx_model/ResNet50.onnx",
        "./onnx_graph_optimized_model/ResNet50_optimized.onnx",
    ),
    (
        "./onnx_model/ResNet50V2.onnx",
        "./onnx_graph_optimized_model/ResNet50V2_optimized.onnx",
    ),
    ("./onnx_model/VGG16.onnx", "./onnx_graph_optimized_model/VGG16_optimized.onnx"),
    (
        "./onnx_model/Xception.onnx",
        "./onnx_graph_optimized_model/Xception_optimized.onnx",
    ),
]

optimized_dir = "./onnx_graph_optimized_model"
os.makedirs(optimized_dir, exist_ok=True)

for model_path, optimized_path in models:
    print(f"Optimizing model: {model_path}")

    sess_options = rt.SessionOptions()
    sess_options.graph_optimization_level = rt.GraphOptimizationLevel.ORT_ENABLE_ALL
    sess_options.optimized_model_filepath = optimized_path
    session = rt.InferenceSession(model_path, sess_options)

    print(f"Optimized model saved to: {optimized_path}")

print("All models optimized and saved successfully.")
