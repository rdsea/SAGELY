from enum import Enum

from pydantic import BaseModel


class ImageClassificationModelEnum(Enum):
    DenseNet121 = "DenseNet121"
    DenseNet201 = "DenseNet201"
    EfficientNetB0 = "EfficientNetB0"
    EfficientNetB7 = "EfficientNetB7"
    EfficientNetV2L = "EfficientNetV2L"
    EfficientNetV2S = "EfficientNetV2S"
    InceptionResNetV2 = "InceptionResNetV2"
    InceptionV3 = "InceptionV3"
    MobileNet = "MobileNet"
    MobileNetV2 = "MobileNetV2"
    NASNetLarge = "NASNetLarge"
    NASNetMobile = "NASNetMobile"
    ResNet50 = "ResNet50"
    ResNet50V2 = "ResNet50V2"
    VGG16 = "VGG16"
    Xception = "Xception"


class ModelConfig(BaseModel):
    input_shape: tuple[int, int, int, int]
    input_mode: str


class InferenceServiceConfig(BaseModel):
    pipeline_id: str
    ensemble: bool
    model_config_dict: dict[ImageClassificationModelEnum, ModelConfig]
    external_services: dict
