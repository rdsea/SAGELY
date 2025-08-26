# from fastapi import FastAPI, HTTPException
# import asyncio
from typing import Optional
import aiohttp
import duckdb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import logging

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
# URL_POLICY_PLANNER = "http://192.168.49.2/policy-planner"
URL_POLICY_PLANNER = "http://policy-planner:8000/policy-planner"
# Connect to DuckDB database or create it if it does not exist
conn = duckdb.connect("context-management.db")


# Models for leader notification, counter update, and commands
class LeaderMessage(BaseModel):
    leader_id: str
    group_id: str


class CounterMessage(BaseModel):
    leader_id: str
    group_id: str
    counter: int


class ChangeGroupOrIDCommand(BaseModel):
    new_group_id: Optional[str] = None
    new_node_id: Optional[str] = None


class ChangeTaskParameterCommand(BaseModel):
    counter_increment: Optional[int] = None


# Create necessary tables
conn.execute("""
CREATE TABLE IF NOT EXISTS counters (
    group_id STRING PRIMARY KEY,
    leader_id STRING,
    counter_value INTEGER
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS commands (
    leader_id STRING,
    command_type STRING,
    command_data STRING
)
""")


@app.post("/notify-context")
# @app.post("/notify-leader")
async def notify_leader_context(message: LeaderMessage):
    try:
        # current_leaders[message.group_id] = message.leader_id
        conn.execute(
            "INSERT INTO counters (group_id, leader_id, counter_value) VALUES (?, ?, ?) "
            "ON CONFLICT(group_id) DO UPDATE SET leader_id=excluded.leader_id, counter_value=excluded.counter_value",
            (message.group_id, message.leader_id, 0),
        )
        print(
            f"Received new leader notification for group {message.group_id}: {message.leader_id}"
        )
        return {"message": "Leader updated successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-counter")
async def update_counter(update: CounterMessage):
    # global counters
    # logger.info(
    #     f"Counter for group {update.group_id} updated to {update.counter} by leader {update.leader_id}"
    # )
    current_leader_record = conn.execute(
        "SELECT leader_id FROM counters WHERE group_id = ?",
        (update.group_id,),
    ).fetchone()

    current_leader = current_leader_record[0] if current_leader_record else None

    if current_leader is None:
        conn.execute(
            "INSERT INTO counters (group_id, leader_id, counter_value) VALUES (?, ?, ?) "
            "ON CONFLICT(group_id) DO UPDATE SET leader_id=excluded.leader_id, counter_value=excluded.counter_value",
            (update.group_id, update.leader_id, 0),
        )
        raise HTTPException(status_code=404, detail="Group not found")

    print(f"current leader: {current_leader}, update leader: {update.leader_id}")

    if current_leader != update.leader_id:
        raise HTTPException(
            status_code=400, detail="Only leader can update the counter"
        )

    conn.execute(
        "UPDATE counters SET counter_value = ? WHERE group_id = ?",
        (update.counter, update.group_id),
    )

    print(
        f"Counter for group {update.group_id} updated to {update.counter} by leader {update.leader_id}"
    )
    return {"message": "Counter updated"}


@app.get("/get-counter")
async def get_counter(group_id: str):
    # global counters

    counter_value = conn.execute(
        "SELECT counter_value FROM counters WHERE group_id = ?",
        (group_id,),
    ).fetchone()

    if counter_value is None:
        counter_value = 0

    print(f"value: {counter_value}")
    return {"counter": counter_value}


@app.get("/get-leader")
async def get_leader(group_id: str):
    leader_value = conn.execute(
        "SELECT leader_id FROM counters WHERE group_id = ?",
        (group_id,),
    ).fetchone()

    if leader_value is None:
        leader_value = None

    print(f"value: {leader_value}")
    return {"leader_id": leader_value}


@app.post("/send-command/change-group-or-id")
async def send_change_group_or_id_command(
    command: ChangeGroupOrIDCommand, target_node_id: str
):
    try:
        command_type = "change-group-or-id"
        command_data = command.json()
        conn.execute(
            "INSERT INTO commands (leader_id, command_type, command_data) VALUES (?, ?, ?) ",
            # "ON CONFLICT(leader_id, command_type) DO UPDATE SET command_data=excluded.command_data",
            (target_node_id, command_type, command_data),
        )
        print(
            f"Command sent to change group or ID for node {target_node_id}: {command_data}"
        )
        return {"message": f"{command_type} command sent"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/send-command/change-task-parameter")
async def send_change_task_parameter_command(
    command: ChangeTaskParameterCommand, target_group_id: str
):
    try:
        current_leader = conn.execute(
            "SELECT leader_id FROM counters WHERE group_id = ?",
            (target_group_id,),
        ).fetchone()

        command_type = "change-task-parameter"
        command_data = command.json()
        conn.execute(
            "INSERT INTO commands (leader_id, command_type, command_data) VALUES (?, ?, ?) "
            "ON CONFLICT(node_id, command_type) DO UPDATE SET command_data=excluded.command_data",
            (current_leader, command_type, command_data),
        )
        print(
            f"Command sent to change group or ID for node {current_leader}: {command_data}"
        )
        return {"message": f"{command_type} command sent"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @app.get("/get-command/{leader_id}/{command_type}")
# async def get_node_command(leader_id: str, command_type: str):
#     # command = commands.get(node_id, {}).get(command_type, None)
#     command = conn.execute(
#         "SELECT command_data FROM commands WHERE leader_id = ? AND command_type = ?",
#         (leader_id, command_type),
#     ).fetchone()
#
#     if command:
#         return {"command": command}
#     else:
#         raise HTTPException(status_code=404, detail="Command not found")
@app.get("/get-command/{leader_id}/{command_type}")
async def get_node_command(leader_id: str, command_type: str):
    rows = conn.execute(
        "SELECT command_data FROM commands WHERE leader_id = ? AND command_type = ?",
        (leader_id, command_type),
    ).fetchall()
    # Return a list of strings; client already knows how to consume this shape
    return {"command": [r[0] for r in rows]}


@app.delete("/get-command/{leader_id}/{command_type}")
async def delete_node_command(leader_id: str, command_type: str):
    try:
        command = conn.execute(
            "SELECT command_data FROM commands WHERE leader_id = ? AND command_type = ?",
            (leader_id, command_type),
        ).fetchone()
        if command:
            conn.execute(
                "DELETE FROM commands WHERE leader_id = ? AND command_type = ?",
                (leader_id, command_type),
            )
            print(f"Command {command_type} for node {leader_id} deleted")
            return {"message": f"Command {command_type} deleted"}
        else:
            raise HTTPException(status_code=404, detail="Command not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def get_group_with_max_counter() -> str:
    row = conn.execute(
        "SELECT group_id FROM counters ORDER BY counter_value DESC LIMIT 1"
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No group found")
    return row[0]


@app.post("/abnormal")
async def abnormal_detection(group_id: str, reason: str = "Abnormal event detected"):
    """
    Detects an anomaly, packages it as context, and sends it to the policy_planner service.
    """
    logger.info(f"Abnormal event detected for group '{group_id}'. Reason: {reason}")

    # Define the context payload for the planner
    anomaly_context = {
        "anomaly_type": "Abnormal Counter Behavior",
        "source": f"context-management-service",
        "details": {"group_id": group_id, "trigger_reason": reason},
    }

    # Send the context to the policy planner
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(URL_POLICY_PLANNER, json=anomaly_context)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            logger.info(
                f"Successfully forwarded abnormal context to policy-planner. Response: {response.json()}"
            )
            return {
                "status": "success",
                "message": "Anomaly reported to planner successfully.",
            }
    except httpx.RequestError as e:
        logger.error(f"Failed to send abnormal context to policy-planner: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to downstream policy-planner service: {e}",
        )


# @app.post("/abnormal")
# async def abnormal_detection(target_leader_id: str, group_id: str):
#     new_group_id = str(get_leader_with_max_counter())
#
#     new_command = ChangeGroupOrIDCommand(
#         new_group_id=new_group_id, new_node_id=target_leader_id
#     )
#     await send_change_group_or_id_command(
#         target_node_id=target_leader_id, command=new_command
#     )
#
#     # request change policy
#     #
#     headers = {
#         "Content-Type": "application/json",
#         "Authorization": "Basic admin:admin",
#     }
#     payload = {"new_group_id": new_group_id, "leader_id": target_leader_id}
#
#     async with aiohttp.ClientSession() as session:
#         async with session.post(
#             URL_POLICY_PLANNER, data=json.dumps(payload), headers=headers
#         ) as response:
#             if response.status == 200:
#                 print(
#                     f"Sent policy-planner change from {target_leader_id} to {group_id}"
#                 )
#             else:
#                 print(
#                     f"Failed to send crash notification {group_id}. Status code: {response.status}"
#                 )
#
#
# # select the fastest one
# async def get_leader_with_max_counter():
#     try:
#         result = conn.execute(
#             "SELECT leader_id FROM counters ORDER BY counter_value DESC LIMIT 1"
#         )
#         if result:
#             return {"leader_id": result}
#         else:
#             raise HTTPException(status_code=404, detail="No leader found")
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
