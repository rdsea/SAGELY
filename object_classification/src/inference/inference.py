import logging
import os
import signal
import sys

import numpy as np
import yaml
from datamodel import ImageClassificationModelEnum, InferenceServiceConfig
from fastapi import FastAPI, Request
from image_classification_agent import ImageClassificationAgent
from opentelemetry import trace

# from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

current_directory = os.path.dirname(os.path.abspath(__file__))
util_directory = os.path.join(current_directory, "..", "util")
sys.path.append(util_directory)

# TODO: find better way please!!!
import utils  # noqa: E402
from consul import ConsulClient  # noqa: E402

chosen_model = os.environ["CHOSEN_MODEL"]
resource = Resource(attributes={SERVICE_NAME: f"inference_{chosen_model}"})

traceProvider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
)
traceProvider.add_span_processor(processor)
trace.set_tracer_provider(traceProvider)
tracer = trace.get_tracer(__name__)

# reader = PeriodicExportingMetricReader(
#     OTLPMetricExporter(endpoint="http://localhost:4318/v1/metrics")
# )
# meterProvider = MeterProvider(resource=resource, metric_readers=[reader])
# metrics.set_meter_provider(meterProvider)
PORT = int(os.environ["PORT"])

# NOTE: model config in the inference service config
#
MODEL_CONFIG = {
    "DenseNet121": [(1, 224, 224, 3), "torch"],
    "DenseNet201": [(1, 224, 224, 3), "torch"],
    "EfficientNetB0": [(1, 224, 224, 3), "raw"],
    "EfficientNetB7": [(1, 600, 600, 3), "raw"],
    "EfficientNetV2L": [(1, 480, 480, 3), "raw"],
    "EfficientNetV2S": [(1, 384, 384, 3), "raw"],
    "InceptionResNetV2": [(1, 299, 299, 3), "tf"],
    "InceptionV3": [(1, 299, 299, 3), "tf"],
    "MobileNet": [(1, 224, 224, 3), "tf"],
    "MobileNetV2": [(1, 224, 224, 3), "tf"],
    "NASNetLarge": [(1, 331, 331, 3), "tf"],
    "NASNetMobile": [(1, 224, 224, 3), "tf"],
    "ResNet50": [(1, 224, 224, 3), "caffe"],
    "ResNet50V2": [(1, 224, 224, 3), "tf"],
    "VGG16": [(1, 224, 224, 3), "caffe"],
    "Xception": [(1, 299, 299, 3), "tf"],
}

try:
    with open("./inference_service_config.yaml") as file:
        yaml_content = yaml.safe_load(file)  # Load YAML content
        config = InferenceServiceConfig(**yaml_content)  # Parse using Pydantic model
except Exception as e:
    logging.error(f"Error loading config file: {e}")
    sys.exit(1)
logging.info(f"Inference configuration: {config}")

local_ip = utils.get_local_ip()
consul_client = ConsulClient(
    config=config.external_services["service_registry"]["consul_config"]
)

chosen_model = ImageClassificationModelEnum[chosen_model]
service_id = consul_client.service_register(
    name=chosen_model.name,
    address=local_ip,
    tag=["nii_case", "inference", chosen_model.name],
    port=PORT,
)

model_config = config.model_config_dict[chosen_model]
ml_agent = ImageClassificationAgent(chosen_model, model_config)

app = FastAPI()


@app.post("/inference")
async def inference(request: Request):
    image_bytes = await request.body()

    # headers = dict(request.headers)
    # carrier = {"traceparent": headers["traceparent"]}
    # ctx = TraceContextTextMapPropagator().extract(carrier=carrier)
    # print(f"Received context: {ctx}")
    #
    # b2 = {"baggage": headers["baggage"]}
    # ctx2 = W3CBaggagePropagator().extract(b2, context=ctx)
    # print(f"Received context2: {ctx2}")
    # logging.info(image_bytes)
    with tracer.start_span("inference"):
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        # NOTE: Here we assume that the processing service has reshape the input image to size 224,224,3
        reconstructed_image = image_array.reshape((224, 224, 3))
        return ml_agent.predict(reconstructed_image)


def signal_handler(sig, frame):
    print("You pressed Ctrl+C! Gracefully shutting down.")
    consul_client.service_deregister(id=service_id)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
FastAPIInstrumentor.instrument_app(
    app,
)
