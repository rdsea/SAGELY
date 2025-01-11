from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

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

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
