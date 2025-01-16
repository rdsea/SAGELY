#from fastapi import FastAPI, HTTPException
from fastapi import FastAPI, HTTPException, UploadFile, status
from pydantic import BaseModel
from typing import Dict, Optional

from opentelemetry import trace

from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# from opentelemetry.sdk.metrics import MeterProvider
# from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

import asyncio, time, logging, aiohttp

AioHttpClientInstrumentor().instrument()
# Service name is required for most backends
resource = Resource(attributes={SERVICE_NAME: "preprocessing"})

traceProvider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://jaeger:4318/v1/traces")
)
traceProvider.add_span_processor(processor)
trace.set_tracer_provider(traceProvider)


tracer = trace.get_tracer(__name__)
app = FastAPI()  # Initialize FastAPI

# Models for leader notification, counter update, and commands
class LeaderMessage(BaseModel):
    leader_id: str
    group_id: str

class CounterUpdate(BaseModel):
    leader_id: str
    group_id: str
    counter: int

class ChangeGroupOrIDCommand(BaseModel):
    new_group_id: Optional[str] = None
    new_node_id: Optional[str] = None

class ChangeTaskParameterCommand(BaseModel):
    counter_increment: Optional[int] = None

# Dictionary to store counter values for each group
counters: Dict[str, int] = {}
# Dictionary to store current leader info for each group
current_leaders: Dict[str, str] = {}
# Dictionary to store commands for each node
commands: Dict[str, Dict[str, str]] = {}  # commands[node_id][command_type] = command_data

@app.post("/notify-leader")
async def notify_leader(message: LeaderMessage):
    global current_leaders
    current_leaders[message.group_id] = message.leader_id
    print(f"Received new leader notification for group {message.group_id}: {message.leader_id}")
    return {"message": "Leader updated successfully"}

@app.post("/heartbeat")
async def heartbeat(message: LeaderMessage):
    if current_leaders.get(message.group_id) == message.leader_id:
        print(f"Received heartbeat from leader {message.leader_id} of group {message.group_id}")
        return {"message": "Heartbeat received"}
    else:
        print(f"Received heartbeat from non-leader or unknown leader {message.leader_id} of group {message.group_id}")
        raise HTTPException(status_code=400, detail="Unknown leader or leader mismatch")

@app.post("/update-counter")
async def update_counter(update: CounterUpdate):
    if current_leaders.get(update.group_id) != update.leader_id:
        raise HTTPException(status_code=400, detail="Only leader can update the counter")
    
    if update.group_id not in counters:
        counters[update.group_id] = 0
    
    counters[update.group_id] = update.counter
    print(f"Counter for group {update.group_id} updated to {update.counter} by leader {update.leader_id}")
    return {"message": "Counter updated"}

@app.get("/get-counter")
async def get_counter(group_id: str):
    if group_id not in counters:
        counters[group_id] = 0
    return {"counter": counters[group_id]}

@app.post("/send-command/change-group-or-id")
async def send_change_group_or_id_command(command: ChangeGroupOrIDCommand, target_node_id: str):
    command_type = "change-group-or-id"
    if target_node_id not in commands:
        commands[target_node_id] = {}
    commands[target_node_id][command_type] = command.model_dump_json()
    print(f"Command sent to change group or ID for node {target_node_id}: {command.model_dump_json()}")
    return {"message": f"{command_type} command sent"}

@app.post("/send-command/change-task-parameter")
async def send_change_task_parameter_command(command: ChangeTaskParameterCommand, target_group_id: str):
    command_type = "change-task-parameter"
    if target_group_id not in commands:
        commands[target_group_id] = {}
    commands[target_group_id][command_type] = command.model_dump_json()
    print(f"Command sent to change task parameter for group {target_group_id}: {command.model_dump_json()}")
    return {"message": f"{command_type} command sent"}

@app.get("/get-command/{node_id}/{command_type}")
async def get_node_command(node_id: str, command_type: str):
    command = commands.get(node_id, {}).get(command_type, None)
    if command:
        return {"command": command}
    else:
        raise HTTPException(status_code=404, detail="Command not found")

@app.delete("/get-command/{node_id}/{command_type}")
async def delete_node_command(node_id: str, command_type: str):
    if node_id in commands and command_type in commands[node_id]:
        del commands[node_id][command_type]
        print(f"Command {command_type} for node {node_id} deleted")
        return {"message": f"Command {command_type} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Command not found")

# Clean up commands when starting the server
@app.on_event("startup")
async def startup_event():
    global commands
    commands = {}  # Initialize or clean up commands

@app.post("/preprocessing/")
async def processing_image(file: UploadFile):
    start_time = time.time()
    preprocessing_url = "http://preprocessing:5010/preprocessing/"
    logging.info(f"Request received in {(time.time() - start_time) * 1000} ms")

    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
            logging.info(f"Forwarding request to {preprocessing_url}")

            form = aiohttp.FormData()
            form.add_field('file', await file.read(), filename=file.filename, content_type=file.content_type)

            async with session.post(preprocessing_url, data=form) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Failed to send image to preprocessing service. Status code: {response.status}",
                    )
                response_data = await response.json()
                logging.info(f"Response received in {(time.time() - start_time) * 1000} ms")
                return response_data

    except aiohttp.ClientError as e:
        logging.error(f"Client error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to connect to preprocessing service.",
        )
    except asyncio.TimeoutError:
        logging.error("Request to preprocessing service timed out.")
        raise HTTPException(
            status_code=500,
            detail="Request to preprocessing service timed out.",
        )
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred.",
        )
FastAPIInstrumentor.instrument_app(app)
