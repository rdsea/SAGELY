# from fastapi import FastAPI, HTTPException
import asyncio
import aiohttp
import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
from typing import Dict

# imulate a ground control station

app = FastAPI()

current_leaders: Dict[str, str] = {}
# Timeout duration in seconds
HEARTBEAT_TIMEOUT = 4
# Store last heartbeat timestamps
last_heartbeat: Dict[str, datetime] = {}
# Background task status flags
monitoring: Dict[str, bool] = {}
URL_NOTI_CRASH = "http://192.168.49.2/abnormal-detect"
CONTEXT_MANAGEMENT_SERVICE_URL = "http://192.168.49.2/notify-context"


# Models for leader notification, counter update, and commands
class LeaderMessage(BaseModel):
    leader_id: str
    group_id: str


@app.post("/notify-leader")
async def notify_leader(request: Request, message: LeaderMessage):
    global current_leaders, monitoring

    # Forward the received message to /notify-leader-context
    await forward_request_to_context(request, message)

    current_leaders[message.group_id] = message.leader_id
    last_heartbeat[message.group_id] = datetime.now()

    if not monitoring.get(message.group_id, False):
        monitoring[message.group_id] = True
        asyncio.create_task(monitor_heartbeat(message.group_id))

    print(
        f"Received new leader notification for group {message.group_id}: {message.leader_id}"
    )

    return {"message": "Leader updated successfully"}


async def forward_request_to_context(request: Request, message: LeaderMessage):
    # Extract headers from the incoming request
    # headers = dict(request.headers)
    headers = {
        k: v for k, v in request.headers.items() if k.lower() != "content-length"
    }  # Exclude Content-Length
    print(f"Forwarding headers: {headers}")  # Debug statement
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                CONTEXT_MANAGEMENT_SERVICE_URL,
                json=message.dict(),
                headers=headers,  # Including the original headers
            )
            response.raise_for_status()
            print(f"Forwarded to context-management-service: {response.json()}")
        except httpx.HTTPStatusError as e:
            print(f"Failed to forward to context-management-service: {str(e)}")
        except Exception as e:
            print(f"An error occurred while forwarding the request: {str(e)}")


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
            f"Received heartbeat from non-leader {message.leader_id} of group {message.group_id}"
        )
        raise HTTPException(status_code=200, detail="Unknown leader or leader mismatch")


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
            await send_command_on_leader_crash(group_id, current_leaders[group_id])
            return


async def send_command_on_leader_crash(group_id: str, leader_id: str):
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Basic admin:admin",
    }
    payload = {"group_id": group_id, "leader_id": leader_id}
    url = URL_NOTI_CRASH

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, data=json.dumps(payload), headers=headers
        ) as response:
            if response.status == 200:
                print(f"Sent crash notification {group_id}")
            else:
                print(
                    f"Failed to send crash notification {group_id}. Status code: {response.status}"
                )
