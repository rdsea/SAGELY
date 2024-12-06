from __future__ import annotations
from functools import cache

import asyncio
import logging
import os
import sys
from typing import Annotated

import aiohttp
from fastapi import BackgroundTasks, FastAPI, Form, Request
from fastapi.responses import JSONResponse
from opentelemetry import trace

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


# Enable instrumentation
AioHttpClientInstrumentor().instrument()
current_directory = os.path.dirname(os.path.abspath(__file__))
util_directory = os.path.join(current_directory, "..", "util")
sys.path.append(util_directory)

# TODO: find better way please!!!
import utils  # noqa: E402

resource = Resource(attributes={SERVICE_NAME: "ensemble"})

traceProvider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://jaeger:4318/v1/traces")
)
traceProvider.add_span_processor(processor)
trace.set_tracer_provider(traceProvider)
tracer = trace.get_tracer(__name__)
config_lock = asyncio.Lock()  # Lock to control access to the global variable


config_file = "ensemble_service.yaml"
config = utils.load_config(file_path=config_file)

assert config is not None
logging.debug(f"Ensemble Service configuration: {config}")

app = FastAPI()
app.state.config = config


async def send_post_request(
    session: aiohttp.ClientSession, url: str, image_data: bytes
):
    async with session.post(url, data=image_data) as response:
        return await response.json()  # Assuming the response is JSON


def get_inference_service_url(ensemble_chosen: list[str]):
    return [f"http://{item.lower()}-service:5012/inference" for item in ensemble_chosen]


async def process_image_task(image_data: bytes, request_id: str):
    # current_span = trace.get_current_span()
    ensemble = app.state.config["ensemble"]
    # chosen_ensemble_function = getattr(
    #     ensemble_function,
    #     app.state.config["aggregating"]["aggregating_func"]["func_name"],
    # )
    list_service_url = get_inference_service_url(ensemble)
    logging.info(f"List service url: {list_service_url}")

    if list_service_url:
        async with aiohttp.ClientSession(trust_env=True) as session:
            tasks = [
                asyncio.create_task(send_post_request(session, url, image_data))
                for url in list_service_url
            ]
            done, _ = await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)

            results = []
            for task in done:
                results.append(await task)
            print(results)
            # print(chosen_ensemble_function(results, request_id))

    else:
        raise RuntimeError("No inference service url")


@app.post("/ensemble_service/")
async def ensemble(
    request: Request,
    background_tasks: BackgroundTasks,
):
    try:
        image_bytes = await request.body()
        request_id = request.query_params["request_id"]
        # logging.info(image_bytes)
        background_tasks.add_task(process_image_task, image_bytes, request_id)

        response = "Success to add image to Ensemble Service"
        return JSONResponse(content={"response": response}, status_code=200)
    except Exception as e:
        logging.exception(f"Error: {e}")
        return JSONResponse(content={"error": f"Error: {e}"}, status_code=500)


@app.post("/change_config")
async def change_requirement(configuration: Annotated[dict, Form()]):
    try:
        async with config_lock:
            app.state.config = configuration
            response = f"Change ensemble to: {configuration} successfully"
            return JSONResponse(content={"response": response}, status_code=200)
    except Exception as e:
        logging.exception(f"Error: {e}")
        return JSONResponse(content={"error": f"Error: {e}"}, status_code=500)


FastAPIInstrumentor.instrument_app(app)
