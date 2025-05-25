import requests
import time
import json

# List of OPA server addresses
opa_servers = [
    "http://localhost:8181/v1/policies/policy.rego",
    # Add more OPA server addresses as needed
]

# Path to the policy file
policy_file_path = "./policy/policy.rego"

# Read the policy file
try:
    with open(policy_file_path, "rb") as file:
        policy_data = file.read()
except FileNotFoundError:
    print(f"Error: The file {policy_file_path} does not exist.")
    exit(1)

results = []

# Send the policy file to each OPA server and measure the time taken
for opa_server in opa_servers:
    try:
        start_time = time.time()  # Record the start time

        response = requests.put(opa_server, data=policy_data)

        if response.status_code == 200:
            # Measure the time taken to apply the policy
            put_duration = time.time() - start_time

            # Verify that the policy has been applied
            verify_start_time = time.time()  # Record the verification start time
            verify_response = requests.get(opa_server)
            verify_duration = (
                time.time() - verify_start_time
            )  # Measure time taken for verification

            if verify_response.status_code == 200:
                # Extract the raw policy from the verification response
                verify_policy_data = json.loads(verify_response.content)["result"][
                    "raw"
                ].encode()

                if verify_policy_data == policy_data:
                    total_duration = (
                        put_duration + verify_duration
                    )  # Total execution time
                    results.append(
                        f"Successfully updated and verified policy on {opa_server} in {total_duration:.6f} seconds."
                    )
                else:
                    results.append(
                        f"Policy update on {opa_server} succeeded, but verification failed. PUT duration: {put_duration:.6f} seconds, Verification duration: {verify_duration:.6f} seconds."
                    )
            else:
                results.append(
                    f"Policy update on {opa_server} succeeded, but verification failed: {verify_response.status_code}. PUT duration: {put_duration:.6f} seconds, Verification duration: {verify_duration:.6f} seconds."
                )
        else:
            results.append(
                f"Failed to update policy on {opa_server}: {response.status_code} - {response.text}"
            )
    except requests.exceptions.RequestException as e:
        results.append(f"Error updating policy on {opa_server}: {str(e)}")

# Print the results
for result in results:
    print(result)
