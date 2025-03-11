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
EDGE_SERVER_URL = "http://192.168.49.2"
EDGE_SERVER_NOTIFY_URL = EDGE_SERVER_URL + "/notify-leader"
EDGE_SERVER_HEARTBEAT_URL = EDGE_SERVER_URL + "/heartbeat"
EDGE_SERVER_UPDATE_COUNTER_URL = EDGE_SERVER_URL + "/update-counter"
EDGE_SERVER_GET_COUNTER_URL = EDGE_SERVER_URL + "/get-counter"
EDGE_SERVER_GET_COMMAND_URL = EDGE_SERVER_URL + "/get-command"

# turn the message to a local fastapi
GCS_FASTAPI_URL = "http://127.0.0.1:8000"

# Define URL mapping
URL_MAPPING = {
    "HEARTBEAT": EDGE_SERVER_HEARTBEAT_URL,
    "LEADER_NOTI": EDGE_SERVER_NOTIFY_URL,
    "UPDATE_COUNTER": EDGE_SERVER_UPDATE_COUNTER_URL,
    "GET_COUNTER": EDGE_SERVER_GET_COUNTER_URL,
    "GET_COMMAND": EDGE_SERVER_GET_COMMAND_URL,
    # Add more mappings as needed
}


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

            mav_type = message.get_type()  # Get the MAVLink message type
            url = URL_MAPPING.get(
                mav_type, EDGE_SERVER_NOTIFY_URL
            )  # Determine URL based on message type

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    response.raise_for_status()
                    print(
                        f"Message of type {mav_type} forwarded to {url} successfully."
                    )
        except Exception as e:
            print(f"Exception occurred while forwarding message: {e}")

    while True:
        msg = mav_conn.recv_match(blocking=True)
        if msg:
            print(f"Received message: {msg}")
            asyncio.run_coroutine_threadsafe(forward_message_to_fastapi(msg), loop)

        #     async with aiohttp.ClientSession() as session:
        #         async with session.post(
        #             f"{GCS_FASTAPI_URL}/receive-mavlink", json=payload, headers=headers
        #         ) as response:
        #             response.raise_for_status()
        #             print("Message forwarded to FastAPI successfully.")
        # except Exception as e:
        #     print(f"Exception occurred while forwarding message: {e}")

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

# import socket
# import requests
#
# # Set up client for GCS communication
# GCS_IP = 'localhost'  # Assuming GCS script is running locally
# GCS_PORT = 14550      # Replace with actual port
# s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#
# # Edge server
# EDGE_SERVER_IP = 'http://edge.server.ip:8000'  # Replace with actual IP and port of the edge server
#
# # Helper function to send a POST request to the FastAPI server
# def send_post_request(endpoint, data):
#     url = f"{EDGE_SERVER_IP}{endpoint}"
#     try:
#         response = requests.post(url, json=data)
#         if response.status_code == 200:
#             print(f"Response from edge server: {response.json()}")
#         else:
#             print(f"Failed to send data to edge server: {response.text}")
#     except requests.exceptions.RequestException as e:
#         print(f"An error occurred: {e}")
#
# while True:
#     data, addr = s.recvfrom(1024)
#     print(f"Received message from GCS: {data.decode('utf-8')}")
#
#     # Define the payload for the POST request
#     payload = {
#         "group_id": 1,  # Example group ID
#         "leader_id": data.decode('utf-8')  # Assuming the received data is the leader ID
#     }
#
#     # Send the payload to the desired endpoint on the FastAPI server
#     send_post_request('/notify-leader', payload)
#     send_post_request('/heartbeat', payload)
