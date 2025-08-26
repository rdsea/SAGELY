import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List


class ExecutionStep(BaseModel):
    action: str = Field(
        ...,
        description="The specific action to execute.",
        example="kubectl apply -f deployment.yaml",
    )
    details: dict = Field(
        default_factory=dict, description="Additional details for the action."
    )


app = FastAPI(
    title="Policy Change Management Service",
    description="Executes the final, concrete steps of a policy change.",
)


@app.post("/execute_change")
async def execute_change(steps: List[ExecutionStep]):
    """
    Receives and 'executes' a list of change management steps.
    In a real system, this would interact with infrastructure APIs.
    """
    print(f"Received request to execute {len(steps)} change step(s)...")
    for i, step in enumerate(steps):
        # In a real implementation, you would execute the action here.
        # For example: run a shell command, call a cloud API, etc.
        print(
            f"  Step {i + 1}: Executing action: '{step.action}' with details: {step.details}"
        )

    # Here you could add logic to verify the change was successful.
    print("All change steps processed.")
    return {"status": "success", "message": f"{len(steps)} steps processed."}
