from typing import Dict, Optional
import asyncio
from fastapi import FastAPI, HTTPException
import duckdb
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI()
# Connect to DuckDB database or create it if it does not exist
conn = duckdb.connect("context.db")

# Create commands table (shared)
conn.execute("""
CREATE TABLE IF NOT EXISTS commands (
    node_id STRING,
    group_id STRING,
    command_type STRING,
    command_data STRING,
    PRIMARY KEY (node_id, command_type)
)
""")


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


class CounterUpdate(BaseModel):
    leader_id: str
    group_id: str
    counter: int


class ChangeGroupOrIDCommand(BaseModel):
    new_group_id: Optional[str] = None
    new_node_id: Optional[str] = None


class ChangeTaskParameterCommand(BaseModel):
    counter_increment: Optional[int] = None


# @app.post("/send-command/change-group-or-id")
# async def send_change_group_or_id_command(command: ChangeGroupOrIDCommand, target_node_id: str):
#     try:
#         command_type = "change-group-or-id"
#         command_data = command.json()
#         conn.execute(
#             "INSERT INTO commands (node_id, group_id, command_type, command_data) VALUES (?, ?, ?) "
#             "ON CONFLICT(node_id, command_type) DO UPDATE SET command_data=excluded.command_data",
#             (target_node_id, command_type, command_data)
#         )
#         print(f"Command sent to change group or ID for node {target_node_id}: {command_data}")
#         return {"message": f"{command_type} command sent"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
# @app.post("/send-command/change-task-parameter")
# async def send_change_task_parameter_command(command: ChangeTaskParameterCommand, target_group_id: str):
#     try:
#         command_type = "change-task-parameter"
#         command_data = command.json()
#         conn.execute(
#             "INSERT INTO commands (node_id, group_id, command_type, command_data) VALUES (?, ?, ?) "
#             "ON CONFLICT(node_id, command_type) DO UPDATE SET command_data=excluded.command_data",
#             (target_group_id, command_type, command_data)
#         )
#         print(f"Command sent to change task parameter for group {target_group_id}: {command_data}")
#         return {"message": f"{command_type} command sent"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#
# @app.get("/get-command/{node_id}/{command_type}")
# async def get_node_command(node_id: str, command_type: str):
#     command = conn.execute(
#         "SELECT command_data FROM commands WHERE node_id = ? AND command_type = ?",
#         (node_id, command_type)
#     ).fetchone()
#
#     if command:
#         return {"command": command[0]}
#     else:
#         raise HTTPException(status_code=404, detail="Command not found")
#
# @app.delete("/get-command/{node_id}/{command_type}")
# async def delete_node_command(node_id: str, command_type: str):
#     try:
#         command = conn.execute(
#             "SELECT command_data FROM commands WHERE node_id = ? AND command_type = ?",
#             (node_id, command_type)
#         ).fetchone()
#
#         if command:
#             conn.execute(
#                 "DELETE FROM commands WHERE node_id = ? AND command_type = ?",
#                 (node_id, command_type)
#             )
#             print(f"Command {command_type} for node {node_id} deleted")
#             return {"message": f"Command {command_type} deleted"}
#         else:
#             raise HTTPException(status_code=404, detail="Command not found")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail:str(e))
#
# @app.post("/update-counter")
# async def update_counter(update: CounterUpdate):
#     try:
#         current_leader = conn.execute(
#             "SELECT leader_id FROM group_info WHERE group_id = ?",
#             (update.group_id,)
#         ).fetchone()
#
#         if current_leader and current_leader[0] != update.leader_id:
#             raise HTTPException(
#                 status_code=400, detail="Only leader can update the counter"
#             )
#
#         conn.execute


@app.post("/send-command/change-group-or-id")
async def send_change_group_or_id_command(
    command: ChangeGroupOrIDCommand, target_node_id: str
):
    try:
        command_type = "change-group-or-id"
        command_data = command.json()
        conn.execute(
            "INSERT INTO commands (node_id, group_id, command_type, command_data) VALUES (?, ?, ?) "
            "ON CONFLICT(node_id, command_type) DO UPDATE SET command_data=excluded.command_data",
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
        command_type = "change-task-parameter"
        command_data = command.json()
        conn.execute(
            "INSERT INTO commands (node_id, group_id, command_type, command_data) VALUES (?, ?, ?) "
            "ON CONFLICT(node_id, command_type) DO UPDATE SET command_data=excluded.command_data",
            (target_group_id, command_type, command_data),
        )
        print(
            f"Command sent to change task parameter for group {target_group_id}: {command_data}"
        )
        return {"message": f"{command_type} command sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-command/{node_id}/{command_type}")
async def get_node_command(node_id: str, command_type: str):
    command = conn.execute(
        "SELECT command_data FROM commands WHERE node_id = ? AND command_type = ?",
        (node_id, command_type),
    ).fetchone()

    if command:
        return {"command": command[0]}
    else:
        raise HTTPException(status_code=404, detail="Command not found")


@app.delete("/get-command/{node_id}/{command_type}")
async def delete_node_command(node_id: str, command_type: str):
    try:
        command = conn.execute(
            "SELECT command_data FROM commands WHERE node_id = ? AND command_type = ?",
            (node_id, command_type),
        ).fetchone()

        if command:
            conn.execute(
                "DELETE FROM commands WHERE node_id = ? AND command_type = ?",
                (node_id, command_type),
            )
            print(f"Command {command_type} for node {node_id} deleted")
            return {"message": f"Command {command_type} deleted"}
        else:
            raise HTTPException(status_code=404, detail="Command not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-counter")
async def update_counter(update: CounterUpdate):
    try:
        current_leader = conn.execute(
            "SELECT leader_id FROM group_info WHERE group_id = ?", (update.group_id,)
        ).fetchone()

        if current_leader and current_leader[0] != update.leader_id:
            raise HTTPException(
                status_code=400, detail="Only leader can update the counter"
            )

        conn.execute(
            "UPDATE group_info SET counter = ? WHERE group_id = ?",
            (update.counter, update.group_id),
        )
        print(
            f"Counter for group {update.group_id} updated to {update.counter} by leader {update.leader_id}"
        )
        return {"message": "Counter updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-counter")
async def get_counter(group_id: str):
    try:
        counter = conn.execute(
            "SELECT counter FROM group_info WHERE group_id = ?", (group_id,)
        ).fetchone()

        if counter:
            return {"counter": counter[0]}
        else:
            return {"counter": 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


################################################################################################
# @app.post("/update-counter")
# async def update_counter(update: CounterUpdate):
#     if current_leaders.get(update.group_id) != update.leader_id:
#         raise HTTPException(
#             status_code=400, detail="Only leader can update the counter"
#         )
#
#     if update.group_id not in counters:
#         counters[update.group_id] = 0
#
#     counters[update.group_id] = update.counter
#     print(
#         f"Counter for group {update.group_id} updated to {update.counter} by leader {update.leader_id}"
#     )
#     return {"message": "Counter updated"}
#
#
# @app.get("/get-counter")
# async def get_counter(group_id: str):
#     if group_id not in counters:
#         counters[group_id] = 0
#     return {"counter": counters[group_id]}
#
#
# # @app.post("/send-command/change-group-or-id")
# # async def send_change_group_or_id_command(
# #     command: ChangeGroupOrIDCommand, target_node_id: str
# # ):
# #     command_type = "change-group-or-id"
# #     if target_node_id not in commands:
# #         commands[target_node_id] = {}
# #     commands[target_node_id][command_type] = command.model_dump_json()
# #     print(
# #         f"Command sent to change group or ID for node {target_node_id}: {command.model_dump_json()}"
# #     )
# #     return {"message": f"{command_type} command sent"}
# #
# # after detecing chnage, asking another support
# #
# @app.post("/send-command/change-group-or-id")
# async def send_change_group_or_id_command(
#     command: ChangeGroupOrIDCommand, target_node_id: str
# ):
#     command_type = "change-group-or-id"
#     if target_node_id not in commands:
#         commands[target_node_id] = {}
#     commands[target_node_id][command_type] = command.json()
#     print(
#         f"Command sent to change group or ID for node {target_node_id}: {command.json()}"
#     )
#     return {"message": f"{command_type} command sent"}
#
#
# @app.post("/send-command/change-task-parameter")
# async def send_change_task_parameter_command(
#     command: ChangeTaskParameterCommand, target_group_id: str
# ):
#     command_type = "change-task-parameter"
#     if target_group_id not in commands:
#         commands[target_group_id] = {}
#     commands[target_group_id][command_type] = command.model_dump_json()
#     print(
#         f"Command sent to change task parameter for group {target_group_id}: {command.model_dump_json()}"
#     )
#     return {"message": f"{command_type} command sent"}
#
#
# @app.get("/get-command/{node_id}/{command_type}")
# async def get_node_command(node_id: str, command_type: str):
#     command = commands.get(node_id, {}).get(command_type, None)
#     if command:
#         return {"command": command}
#     else:
#         raise HTTPException(status_code=404, detail="Command not found")
#
#
# @app.delete("/get-command/{node_id}/{command_type}")
# async def delete_node_command(node_id: str, command_type: str):
#     if node_id in commands and command_type in commands[node_id]:
#         del commands[node_id][command_type]
#         print(f"Command {command_type} for node {node_id} deleted")
#         return {"message": f"Command {command_type} deleted"}
#     else:
#         raise HTTPException(status_code=404, detail="Command not found")
#
#
# # Clean up commands when starting the server
# @app.on_event("startup")
# async def startup_event():
#     global commands
#     commands = {}  # Initialize or clean up commands
