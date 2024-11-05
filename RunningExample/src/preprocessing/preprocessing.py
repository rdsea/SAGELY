import logging
import os
import signal
import sys
import time
from typing import Union
from uuid import uuid4

import aiohttp
import cv2
import numpy as np
from fastapi import FastAPI, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from image_processing_functions import resize
from opentelemetry import trace

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# from opentelemetry.sdk.metrics import MeterProvider
# from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


AioHttpClientInstrumentor().instrument()
# Service name is required for most backends
resource = Resource(attributes={SERVICE_NAME: "preprocessing"})

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
# meter = metrics.get_meter("preprocessing.meter")
# from rohe.common import rohe_utils

# from rohe.storage.minio import MinioConnector

current_directory = os.path.dirname(os.path.abspath(__file__))
util_directory = os.path.join(current_directory, "..", "util")
sys.path.append(util_directory)

import utils  # noqa: E402
from consul import ConsulClient  # noqa: E402

# config_lock = asyncio.Lock()  # Lock to control access to the global variable

PORT = int(os.environ["PORT"])

try:
    port = PORT
    config_file = "preprocessing_config.yaml"
    config = utils.load_config(file_path=config_file)
except Exception as e:
    logging.error(f"Error loading config file: {e}")
    sys.exit(1)
assert config is not None
# logging.info(f"Image Processing configuration: {config}")

# minio_connector = MinioConnector(config["external_services"]["minio_storage"])

local_ip = utils.get_local_ip()
consul_client = ConsulClient(
    config=config["external_services"]["service_registry"]["consul_config"]
)
service_id = consul_client.service_register(
    name="preprocessing", address=local_ip, tag=["nii_case"], port=port
)
# qoa_client = QoaClient(config_dict=config["qoa_config"])
# qoa_client.start_all_probes()


accepted_file_types = [
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/heic",
    "image/heif",
    "image/heics",
    "png",
    "jpeg",
    "jpg",
    "heic",
    "heif",
    "heics",
]


def get_ensemble_service_url() -> Union[str, None]:
    try:
        # get tags and query type for image info service
        tags = config["external_services"]["inference_service"]["tags"]
        query_type = config["external_services"]["inference_service"]["type"]
        ensemble_name = config["external_services"]["inference_service"][
            "ensemble_name"
        ]

        # try 3 times to get image info service
        for _ in range(1, 3):
            ensemble_service_list: dict = utils.handle_service_query(
                consul_client=consul_client,
                service_name=ensemble_name,
                query_type=query_type,
                tags=tags,
            )
            if ensemble_service_list:
                ensemble_service = ensemble_service_list[0]
                ensemble_service_url = f"http://{ensemble_service['Address']}:{ensemble_service['Port']}/ensemble_service/"
                logging.debug(f"Get ensemble url successfully: {ensemble_service_url}")
                return ensemble_service_url
            time.sleep(1)
            logging.info("Waiting for image info service to be available")
        return None
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        return None


app = FastAPI()


@app.get("/test/")
async def get_test():
    """
    return message to client to notify them that they are accessing the correct ingestion server
    """
    response = "This is processing service controller"
    return JSONResponse(content={"response": response}, status_code=200)


def validate_image_type(content_type: Union[str, None]):
    if content_type is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="UploadFile have no content type",
        )
    if content_type not in accepted_file_types:
        logging.info(content_type)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"UploadFile with type {content_type} is not accepted, only accept {accepted_file_types}",
        )


@app.post("/preprocessing")
async def processing_image(file: UploadFile):
    validate_image_type(file.content_type)

    contents = await file.read()
    np_array = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)
    # NOTE: cv2 and Pillow has different color channel layout
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    shape = image.shape
    if shape != (224, 224, 3):
        processed_image = resize(image)
    else:
        processed_image = image

    start_time = time.time()
    ensemble_service_url = get_ensemble_service_url()
    logging.info(f"{(time.time() - start_time)*1000}")
    if ensemble_service_url is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Can't find ensemble service url",
        )
    image_bytes = processed_image.tobytes()
    request_id = str(uuid4())
    # with tracer.start_as_current_span("preprocessing") as _:
    #     ctx = baggage.set_baggage("request_id", request_id)
    #
    #     headers = {}
    #     W3CBaggagePropagator().inject(headers, ctx)
    #     TraceContextTextMapPropagator().inject(headers, ctx)

    # response_time = meter.create_counter(
    #     "work.counter", unit="1", description="Counts the amount of work done"
    # )
    async with aiohttp.ClientSession() as session:
        logging.info(ensemble_service_url)
        async with session.post(
            ensemble_service_url,
            data=image_bytes,
            params={"request_id": request_id},
        ) as response:
            if response.status != 200:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to send image to ensemble service. Status code: {response.status}",
                )
            _ = await response.json()
    return "File accepted"


def signal_handler(sig, frame):
    logging.info("You pressed Ctrl+C! Gracefully shutting down.")
    consul_client.service_deregister(id=service_id)
    sys.exit(0)


# Register the signal handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)
FastAPIInstrumentor.instrument_app(app)
