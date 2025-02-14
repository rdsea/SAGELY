#!/bin/bash
# Model name and according port
# DenseNet121  8050
# DenseNet201 8051
# EfficientNetB0 8052
# EfficientNetB7 8053
# EfficientNetV2L 8054
# EfficientNetV2S 8055
# InceptionResNetV2 8056
# InceptionV3 8057
# MobileNet 8058
# MobileNetV2 8059
# NASNetLarge 8060
# NASNetMobile 8061
# ResNet50 8062
# ResNet50V2 8063
# VGG16 8064
# Xception 8065

echo "Running cpu version"
docker run -p 8058:8058 --net host rdsea/onnx_inference:cpu --model EfficientNetB0
