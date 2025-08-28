# import uvicorn
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# This is a placeholder for your policy generation logic.
# In a real scenario, this would be a more complex module.
def generate_policy(previous_policy: str, context: dict) -> str:
    """Generates a new policy based on old policy and new context."""
    return f"# Policy generated based on anomaly: {context.get('anomaly_type')}\n# Previous policy for reference: {previous_policy}\nallow = true"


# --- Pydantic Models ---
class AnomalyContext(BaseModel):
    anomaly_type: str = Field(..., example="High CPU Usage")
    source: str = Field(..., example="web-server-1")
    details: dict = Field(default_factory=dict)


class PolicyPlan(BaseModel):
    plan_name: str = Field(..., example="Update OPA Policy with new rules.")
    context: dict = Field(
        default_factory=dict,
        description="The original context that triggered the plan.",
    )
    policy_content: str = Field(..., description="The new Rego policy content.")


# --- FastAPI App ---
app = FastAPI(
    title="Policy Planner Service",
    description="Selects a policy and creates a high-level plan based on anomaly context.",
)

COORDINATOR_URL = "http://policy-coordinator:1340/coordinate_plan"


def load_previous_policy() -> str:
    """Placeholder for loading the current policy."""
    # In a real system, this might come from a file, a database, or the coordinator itself.
    return "# Current active policy\nallow = false"


async def develop_and_forward_plan(context: AnomalyContext):
    """The core logic for planning and forwarding."""
    print(
        f"Received anomaly context: '{context.anomaly_type}' from '{context.source}'. Developing a plan..."
    )

    # 1. Load previous policy (using your existing function concept)
    previous_policy = load_previous_policy()

    # 2. Generate new policy (using your existing function concept)
    new_policy_content = generate_policy(previous_policy, context.dict())

    # 3. Create a plan to send to the coordinator
    plan = PolicyPlan(
        plan_name=f"Update OPA Policy for {context.anomaly_type}",
        context=context.dict(),
        policy_content=new_policy_content,
    )

    print(f"Plan '{plan.plan_name}' developed. Sending to Policy Coordinator Service.")

    # 4. Send to coordinator
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(COORDINATOR_URL, json=plan.dict())
            response.raise_for_status()
    except httpx.RequestError as e:
        print(f"Error calling Policy Coordinator Service: {e}")
        raise HTTPException(
            status_code=503, detail=f"Could not connect to downstream service: {e}"
        )

    return {
        "status": "accepted",
        "detail": "Plan developed and forwarded for coordination.",
    }


# --- API Endpoints ---
@app.post("/develop_plan", status_code=202)
async def develop_plan_endpoint(context: AnomalyContext):
    """
    This endpoint is called by the Context Management service.
    It triggers the planning and forwarding logic.
    """
    return await develop_and_forward_plan(context)


@app.post("/trigger_planner_manual")
async def trigger_planner_manual():
    """
    A manual trigger for testing, using dummy context.
    This preserves the concept of your original 'trigger_planner' endpoint.
    """
    dummy_context = AnomalyContext(
        anomaly_type="Manual Trigger",
        source="API call",
        details={"reason": "Manual intervention by operator."},
    )
    return await develop_and_forward_plan(dummy_context)


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=1339)
