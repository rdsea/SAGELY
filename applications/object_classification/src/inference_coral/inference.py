import logging
import os
import sys

import numpy as np
import yaml
from datamodel import ImageClassificationModelEnum, InferenceServiceConfig
from fastapi import FastAPI, Request
from image_classification_agent import ImageClassificationAgent

current_directory = os.path.dirname(os.path.abspath(__file__))
util_directory = os.path.join(current_directory, "..", "util")
sys.path.append(util_directory)

# TODO: find better way please!!!
import utils  # noqa: E402
from consul import ConsulClient  # noqa: E402

PORT = int(os.environ["PORT"])

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

chosen_model = os.environ["CHOSEN_MODEL"]
chosen_model = ImageClassificationModelEnum.from_str(chosen_model)
# service_id = consul_client.service_register(
#     name=chosen_model.name,
#     address=local_ip,
#     tag=["nii_case", "inference", chosen_model.name],
#     port=PORT,
# )

model_config = config.model_config_dict[chosen_model]
ml_agent = ImageClassificationAgent(chosen_model, model_config)

app = FastAPI()


@app.post("/inference")
async def inference(request: Request):
    image_bytes = await request.body()
    image_array = np.frombuffer(image_bytes, dtype=np.float32)
    # NOTE: Here we assume that the processing service has reshape the input image to size 224,224,3
    reconstructed_image = image_array.reshape((224, 224, 3))
    return ml_agent.predict(reconstructed_image)


# def signal_handler(sig, frame):
#     print("You pressed Ctrl+C! Gracefully shutting down.")
#     consul_client.service_deregister(id=service_id)
#     sys.exit(0)
#
#
# signal.signal(signal.SIGINT, signal_handler)
