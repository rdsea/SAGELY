import uvicorn
import httpx
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List
from kubernetes import client, config
from kubernetes.client.rest import ApiException


# --- Pydantic Models ---
class PolicyPlan(BaseModel):
    plan_name: str = Field(..., example="Update OPA Policy with new rules.")
    context: dict = Field(
        default_factory=dict,
        description="The original context that triggered the plan.",
    )
    policy_content: str = Field(..., description="The new Rego policy content.")


class ExecutionStep(BaseModel):
    action: str = Field(
        ...,
        description="The specific action to execute.",
        example="kubectl apply -f deployment.yaml",
    )
    details: dict = Field(
        default_factory=dict, description="Additional details for the action."
    )


# --- FastAPI App ---
app = FastAPI(
    title="Policy Coordinator Service",
    description="Translates high-level plans into concrete, executable steps like updating Kubernetes ConfigMaps.",
)

CHANGE_MANAGEMENT_URL = "http://policy-change-management:1341/execute_change"


# --- Business Logic ---
def update_kubernetes_configmap(policy_content: str):
    """Updates the 'opa-policy' ConfigMap in Kubernetes."""
    try:
        # Assuming in-cluster config, but falls back to kube-config for local dev
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()

        v1 = client.CoreV1Api()
        configmap_name = "opa-policy"
        namespace = "default"
        configmap_body = client.V1ConfigMap(
            api_version="v1",
            kind="ConfigMap",
            metadata=client.V1ObjectMeta(name=configmap_name),
            data={"policy.rego": policy_content},
        )

        try:
            v1.replace_namespaced_config_map(
                name=configmap_name, namespace=namespace, body=configmap_body
            )
            print(f"ConfigMap '{configmap_name}' updated successfully.")
        except ApiException as e:
            if e.status == 404:
                v1.create_namespaced_config_map(
                    namespace=namespace, body=configmap_body
                )
                print(f"ConfigMap '{configmap_name}' created successfully.")
            else:
                raise
        return {
            "status": "success",
            "detail": f"ConfigMap '{configmap_name}' handled successfully.",
        }
    except Exception as e:
        print(f"Error interacting with Kubernetes: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error interacting with Kubernetes: {str(e)}"
        )


# --- API Endpoints ---
@app.post("/coordinate_plan", status_code=202)
async def coordinate_plan(plan: PolicyPlan):
    """
    Receives a high-level plan, executes its primary action (updating a ConfigMap),
    and then forwards execution steps to the change management service.
    """
    print(f"Received plan: '{plan.plan_name}'. Coordinating execution steps...")

    # 1. Execute the primary action defined in your existing logic
    update_result = update_kubernetes_configmap(plan.policy_content)
    print(update_result["detail"])

    # 2. Formulate and forward follow-up steps
    steps = [
        ExecutionStep(action=f"Confirm ConfigMap update for plan: {plan.plan_name}"),
        ExecutionStep(
            action="Verify OPA agent policy reload",
            details={"configmap_name": "opa-policy"},
        ),
    ]
    print(
        f"Coordination complete. Sending {len(steps)} follow-up steps to Change Management Service."
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                CHANGE_MANAGEMENT_URL, json=[step.dict() for step in steps]
            )
            response.raise_for_status()
    except httpx.RequestError as e:
        print(f"Error calling Policy Change Management Service: {e}")
        # Don't raise HTTPException here if the primary task (ConfigMap update) succeeded
        return {
            "status": "accepted_with_downstream_error",
            "detail": "Plan action executed, but failed to forward to change management.",
        }

    return {
        "status": "accepted",
        "detail": "Plan action executed and forwarded for final verification.",
    }


# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=8000)
