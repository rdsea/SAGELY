# def receive_spec_from_planner():
#     pass
#
#
# def discover_policy_enforcer():
#     # failure, retry
#     pass
#
#
# def call_policy_update():
#     pass

import subprocess
import argparse


def update_configmap(policy_path):
    # Ensure correct formatting with the full path
    command = (
        f"kubectl create configmap opa-policy "
        f"--from-file=policy.rego={policy_path} "
        "--dry-run=client -o yaml | "
        "kubectl replace -f -"
    )

    try:
        # Execute the command
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Print the output of the command
        print("Command output:", result.stdout)

    except subprocess.CalledProcessError as e:
        # Print the error if the command failed
        print("Command failed with error:", e.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update OPA policy")
    parser.add_argument("policy_path", help="Path to the policy.rego file")

    args = parser.parse_args()
    update_configmap(args.policy_path)
