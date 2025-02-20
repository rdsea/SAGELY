import asyncio
import threading
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import aiohttp
from pymavlink import mavutil
from threading import Event, Thread, Timer

app = FastAPI()

# Configuration variables (replace with actual values)
EDGE_SERVER_URL = "http://192.168.49.2:8000"
EDGE_SERVER_NOTIFY_URL = EDGE_SERVER_URL + "/notify-leader"
EDGE_SERVER_HEARTBEAT_URL = EDGE_SERVER_URL + "/heartbeat"
EDGE_SERVER_UPDATE_COUNTER_URL = EDGE_SERVER_URL + "/update-counter"
EDGE_SERVER_GET_COUNTER_URL = EDGE_SERVER_URL + "/get-counter"
EDGE_SERVER_GET_COMMAND_URL = EDGE_SERVER_URL + "/get-command"
GCS_FASTAPI_URL = "http://127.0.0.1:8000"


# Pydantic Models
class HeartbeatMessage(BaseModel):
    leader_id: str
    group_id: str


class CounterUpdateMessage(BaseModel):
    leader_id: str
    group_id: str
    counter: int


class MavlinkMessage(BaseModel):
    mavlink_message: dict


# Forwarding function to the edge server
async def forward_to_edge_server(url, data):
    async with aiohttp.ClientSession() as session:
        try:
            headers = {"Content-Type": "application/json"}
            async with session.post(url, json=data, headers=headers) as response:
                response.raise_for_status()
                return {"message": "Success"}
        except aiohttp.ClientError as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/heartbeat")
async def receive_heartbeat(message: HeartbeatMessage):
    data = {"leader_id": message.leader_id, "group_id": message.group_id}
    return await forward_to_edge_server(EDGE_SERVER_HEARTBEAT_URL, data)


@app.post("/update-counter")
async def update_counter(message: CounterUpdateMessage):
    data = {
        "leader_id": message.leader_id,
        "group_id": message.group_id,
        "counter": message.counter,
    }
    return await forward_to_edge_server(EDGE_SERVER_UPDATE_COUNTER_URL, data)


@app.get("/get-counter")
async def get_counter(group_id: str):
    try:
        HEADER = {"Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                EDGE_SERVER_GET_COUNTER_URL,
                headers=HEADER,
                params={"group_id": group_id},
            ) as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete-command/{node_id}/{command_type}")
async def delete_command(node_id: str, command_type: str):
    try:
        HEADER = {"Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{EDGE_SERVER_GET_COMMAND_URL}/{node_id}/{command_type}",
                headers=HEADER,
            ) as response:
                response.raise_for_status()
                return {"message": "Command deleted successfully"}
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/receive-mavlink")
async def receive_mavlink(message: MavlinkMessage):
    print(f"Received MAVLink message: {message.mavlink_message}")
    return {"message": "Received MAVLink message successfully"}


def mavlink_listener(server_ip, server_port, loop):
    mav_conn = mavutil.mavlink_connection(f"udp:{server_ip}:{server_port}")

    async def forward_message_to_fastapi(message):
        try:
            payload = {"mavlink_message": message.to_dict()}
            headers = {"Content-Type": "application/json"}
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{GCS_FASTAPI_URL}/receive-mavlink", json=payload, headers=headers
                ) as response:
                    response.raise_for_status()
                    print("Message forwarded to FastAPI successfully.")
        except Exception as e:
            print(f"Exception occurred while forwarding message: {e}")

    while True:
        msg = mav_conn.recv_match(blocking=True)
        if msg:
            print(f"Received message: {msg}")
            asyncio.run_coroutine_threadsafe(forward_message_to_fastapi(msg), loop)


def start_mavlink_listener():
    server_ip = "0.0.0.0"
    server_port = 14550
    loop = asyncio.get_event_loop()
    threading.Thread(
        target=mavlink_listener, args=(server_ip, server_port, loop)
    ).start()


@app.on_event("startup")
async def startup_event():
    start_mavlink_listener()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
