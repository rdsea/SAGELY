from fastapi import FastAPI, UploadFile, File
import requests
from typing import List

app = FastAPI()

# List of OPA server addresses
opa_servers = [
    "http://localhost:8181/v1/policies/policy.rego",
    # "http://other-opa-server:8181/v1/policies/policy.rego",
    # Add more OPA server addresses as needed
]


@app.post("/update-policy/")
async def update_policy(file: UploadFile = File(...)):
    policy_data = await file.read()
    results = []

    for opa_server in opa_servers:
        try:
            response = requests.put(opa_server, data=policy_data)
            if response.status_code == 200:
                results.append(f"Successfully updated policy on {opa_server}.")
            else:
                results.append(
                    f"Failed to update policy on {opa_server}: {response.status_code} - {response.text}"
                )
        except requests.exceptions.RequestException as e:
            results.append(f"Error updating policy on {opa_server}: {str(e)}")

    return {"results": results}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
