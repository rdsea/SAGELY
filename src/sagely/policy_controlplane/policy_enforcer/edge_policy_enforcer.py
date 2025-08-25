import subprocess


import argparse
import subprocess
import shlex


# def update_configmap(new_policy):
#     # Corrected string interpolation using an f-string
#     command = (
#         f"kubectl create configmap opa-policy "
#         f"--from-file=policy.rego={new_policy} "
#         "--dry-run=client -o yaml | "
#         "kubectl replace -f -"
#     )
def update_configmap(
    rego_path: str, configmap_name: str = "opa-policy", key_name: str = "policy.rego"
):
    # Build the command; quote user-provided values since we're using shell=True
    command = (
        f"kubectl create configmap {shlex.quote(configmap_name)} "
        f"--from-file={shlex.quote(key_name)}={shlex.quote(rego_path)} "
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
        print("Command failed with error:", e.stderr)


if __name__ == "__main__":
    # NOTE: for testing
    # update_configmap(new_policy="new_policy.rego")

    parser = argparse.ArgumentParser(
        description="Update an OPA policy ConfigMap from a Rego file."
    )
    parser.add_argument(
        "rego_path", help="Path to the Rego policy file (e.g., ./new_policy.rego)"
    )
    parser.add_argument(
        "--configmap", default="opa-policy", help="ConfigMap name (default: opa-policy)"
    )
    parser.add_argument(
        "--key",
        default="policy.rego",
        help="Key name inside the ConfigMap (default: policy.rego)",
    )
    args = parser.parse_args()

    update_configmap(
        rego_path=args.rego_path, configmap_name=args.configmap, key_name=args.key
    )
