# from fastapi import FastAPI, HTTPException
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import aiohttp

# from opentelemetry import trace
# from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# from opentelemetry.instrumentation.aiohttp_client import AioHttpClientInstrumentor
# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
#
# # from opentelemetry.sdk.metrics import MeterProvider
# # from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
# from opentelemetry.sdk.resources import SERVICE_NAME, Resource
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor
#
# AioHttpClientInstrumentor().instrument()
# Service name is required for most backends
# resource = Resource(attributes={SERVICE_NAME: "preprocessing"})

# traceProvider = TracerProvider(resource=resource)
# processor = BatchSpanProcessor(
#     OTLPSpanExporter(endpoint="http://jaeger:4318/v1/traces")
# )
# traceProvider.add_span_processor(processor)
# trace.set_tracer_provider(traceProvider)


# tracer = trace.get_tracer(__name__)
app = FastAPI()
# Connect to DuckDB database or create it if it does not exist
# conn = duckdb.connect("service-discovery.db")


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
commands: Dict[
    str, Dict[str, str]
] = {}  # commands[node_id][command_type] = command_data

# Timeout duration in seconds
HEARTBEAT_TIMEOUT = 4
# Store last heartbeat timestamps
last_heartbeat: Dict[str, datetime] = {}
# Background task status flags
monitoring: Dict[str, bool] = {}


# @app.post("/notify-leader")
# async def notify_leader(message: LeaderMessage):
#     global current_leaders
#     current_leaders[message.group_id] = message.leader_id
#     print(
#         f"Received new leader notification for group {message.group_id}: {message.leader_id}"
#     )
#     return {"message": "Leader updated successfully"}
@app.post("/notify-leader")
async def notify_leader(message: LeaderMessage):
    global current_leaders, monitoring

    current_leaders[message.group_id] = message.leader_id
    last_heartbeat[message.group_id] = datetime.now()

    if not monitoring.get(message.group_id, False):
        monitoring[message.group_id] = True
        asyncio.create_task(monitor_heartbeat(message.group_id))

    print(
        f"Received new leader notification for group {message.group_id}: {message.leader_id}"
    )
    return {"message": "Leader updated successfully"}


async def monitor_heartbeat(group_id: str):
    while monitoring.get(group_id, False):
        await asyncio.sleep(HEARTBEAT_TIMEOUT)
        if datetime.now() - last_heartbeat.get(group_id, datetime.min) > timedelta(
            seconds=HEARTBEAT_TIMEOUT
        ):
            print(
                f"Leader in group {group_id} is suspected to have crashed. No heartbeat received for {HEARTBEAT_TIMEOUT} seconds."
            )
            monitoring[group_id] = False
            # Trigger the command to change group or ID
            await send_command_on_leader_crash(group_id)
            return


async def send_command_on_leader_crash(group_id: str):
    new_command = ChangeGroupOrIDCommand(new_group_id="new-group-id")
    target_node_id = "node-2"  # Determine the target node dynamically if needed

    payload = new_command.json()
    headers = {"Content-Type": "application/json"}

    url = f"http://localhost:8080/send-command/change-group-or-id?target_node_id={target_node_id}"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers) as response:
            if response.status == 200:
                print(f"Sent change-group-or-id command to {target_node_id}")
            else:
                print(
                    f"Failed to send change-group-or-id command to {target_node_id}, status: {response.status}, detail: {await response.text()}"
                )


# @app.post("/heartbeat")
# async def heartbeat(message: LeaderMessage):
#     if current_leaders.get(message.group_id) == message.leader_id:
#         print(
#             f"Received heartbeat from leader {message.leader_id} of group {message.group_id}"
#         )
#         return {"message": "Heartbeat received"}
#     else:
#         print(
#             f"Received heartbeat from non-leader or unknown leader {message.leader_id} of group {message.group_id}"
#         )
#         raise HTTPException(status_code=400, detail="Unknown leader or leader mismatch")
@app.post("/heartbeat")
async def heartbeat(message: LeaderMessage):
    if current_leaders.get(message.group_id) == message.leader_id:
        last_heartbeat[message.group_id] = datetime.now()
        print(
            f"Received heartbeat from leader {message.leader_id} of group {message.group_id}"
        )
        return {"message": "Heartbeat received"}
    else:
        print(
            f"Received heartbeat from non-leader or unknown leader {message.leader_id} of group {message.group_id}"
        )
        raise HTTPException(status_code=400, detail="Unknown leader or leader mismatch")


@app.post("/update-counter")
async def update_counter(update: CounterUpdate):
    if current_leaders.get(update.group_id) != update.leader_id:
        raise HTTPException(
            status_code=400, detail="Only leader can update the counter"
        )

    if update.group_id not in counters:
        counters[update.group_id] = 0

    counters[update.group_id] = update.counter
    print(
        f"Counter for group {update.group_id} updated to {update.counter} by leader {update.leader_id}"
    )
    return {"message": "Counter updated"}


@app.get("/get-counter")
async def get_counter(group_id: str):
    if group_id not in counters:
        counters[group_id] = 0
    return {"counter": counters[group_id]}


# @app.post("/send-command/change-group-or-id")
# async def send_change_group_or_id_command(
#     command: ChangeGroupOrIDCommand, target_node_id: str
# ):
#     command_type = "change-group-or-id"
#     if target_node_id not in commands:
#         commands[target_node_id] = {}
#     commands[target_node_id][command_type] = command.model_dump_json()
#     print(
#         f"Command sent to change group or ID for node {target_node_id}: {command.model_dump_json()}"
#     )
#     return {"message": f"{command_type} command sent"}
#
# after detecting change, asking another support
#
@app.post("/send-command/change-group-or-id")
async def send_change_group_or_id_command(
    command: ChangeGroupOrIDCommand, target_node_id: str
):
    command_type = "change-group-or-id"
    if target_node_id not in commands:
        commands[target_node_id] = {}
    commands[target_node_id][command_type] = command.json()
    print(
        f"Command sent to change group or ID for node {target_node_id}: {command.json()}"
    )
    return {"message": f"{command_type} command sent"}


@app.post("/send-command/change-task-parameter")
async def send_change_task_parameter_command(
    command: ChangeTaskParameterCommand, target_group_id: str
):
    command_type = "change-task-parameter"
    if target_group_id not in commands:
        commands[target_group_id] = {}
    commands[target_group_id][command_type] = command.model_dump_json()
    print(
        f"Command sent to change task parameter for group {target_group_id}: {command.model_dump_json()}"
    )
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


# @app.post("/preprocessing-gateway")
# async def processing_image(request: Request):
#     logging.info("enter preprocessing from gateway")
#     start_time = time.time()
#     preprocessing_url = "http://preprocessing-service:5010/preprocessing/"
#
#     logging.info(f"Request received in {(time.time() - start_time) * 1000:.2f} ms")
#
#     try:
#         async with aiohttp.ClientSession(
#             timeout=aiohttp.ClientTimeout(total=60), raise_for_status=True
#         ) as session:
#             logging.info(f"Forwarding request to {preprocessing_url}")
#
#             async with session.request(
#                 method=request.method,
#                 url=preprocessing_url,
#                 headers=request.headers,
#                 data=await request.body(),
#                 allow_redirects=False,  # Do not allow redirects
#             ) as response:
#                 if response.status == 307:
#                     logging.error(
#                         f"Got redirected to: {response.headers.get('Location')}"
#                     )
#                     raise HTTPException(
#                         status_code=response.status,
#                         detail="Unexpected redirect occurred.",
#                     )
#                 response_data = await response.json()
#                 logging.info(
#                     f"Response received in {(time.time() - start_time) * 1000:.2f} ms"
#                 )
#                 return response_data
#
#     except aiohttp.ClientError as e:
#         logging.error(f"Client error: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail="Failed to connect to preprocessing service.",
#         )
#     except asyncio.TimeoutError:
#         logging.error("Request to preprocessing service timed out.")
#         raise HTTPException(
#             status_code=500,
#             detail="Request to preprocessing service timed out.",
#         )
#     except Exception as e:
#         logging.error(f"Unexpected error: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail="An unexpected error occurred.",
#         )


# FastAPIInstrumentor.instrument_app(app)
