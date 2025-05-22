import subprocess
import time
import threading
import argparse
from datetime import datetime


def get_pods(namespace):
    pod_result = subprocess.run(
        [
            "kubectl",
            "get",
            "pods",
            "-n",
            namespace,
            "-o",
            "jsonpath={.items[*].metadata.name}",
        ],
        capture_output=True,
        text=True,
    )
    return pod_result.stdout.split()


def monitor_logs(
    pod_name,
    container_name,
    current_log_id,
    start_event,
    start_time_holder,
    log_identifier,
    sync_kubelet,
    number_services,
    policy_size,
    namespace,  # Add namespace as a parameter
):
    # Wait until the start_event is set
    start_event.wait()
    start_time = start_time_holder[0]
    while True:
        # Capture logs from the pod and look for a new unique ID
        log_command = f"kubectl logs -n {namespace} -c {container_name} {pod_name} --tail=5 | grep {log_identifier} | tail -n 1"
        log_entry = (
            subprocess.check_output(log_command, shell=True).decode("utf-8").strip()
        )

        if log_entry:
            new_log_id = log_entry.split('"')[4]

            # Check if new log entry with different unique ID is found
            if new_log_id != current_log_id:
                end_time = (
                    datetime.utcnow().timestamp() * 1e9
                )  # Current time in nanoseconds
                duration = (end_time - start_time) // 1e6  # Duration in milliseconds
                pod_prefix = pod_name.split("-")[0]
                result_filename = f"{pod_prefix}_{sync_kubelet}_{number_services}_{policy_size}_results.csv"

                with open(result_filename, "a") as results_file:
                    results_file.write(f"{duration}\n")
                break

        time.sleep(0.1)


def main(
    namespace,
    policy_1,
    policy_2,
    sync_kubelet,
    number_services,
    policy_size,
    log_identifier,
):
    pods = get_pods(namespace)

    for i in range(1, 1001):
        policy = policy_1 if i % 2 == 0 else policy_2

        # Initialize the event and holder for start_time
        start_event = threading.Event()
        start_time_holder = [
            None
        ]  # Use a list to hold the start time so it can be referenced in the thread

        threads = []
        for pod in pods:
            # Skip any pods that are not running
            status_result = subprocess.run(
                [
                    "kubectl",
                    "get",
                    "pod",
                    pod,
                    "-n",
                    namespace,
                    "-o",
                    "jsonpath={.status.phase}",
                ],
                capture_output=True,
                text=True,
            )
            status = status_result.stdout.strip()

            if status == "Running":
                print(pod)
                log_command = f"kubectl logs -n {namespace} -c opa-istio {pod} --tail=5 | grep {log_identifier} | tail -n 1"
                current_log_entry = (
                    subprocess.check_output(log_command, shell=True)
                    .decode("utf-8")
                    .strip()
                )
                current_log_id = (
                    current_log_entry.split('"')[4] if current_log_entry else ""
                )
                thread = threading.Thread(
                    target=monitor_logs,
                    args=(
                        pod,
                        "opa-istio",
                        current_log_id,
                        start_event,
                        start_time_holder,
                        log_identifier,
                        sync_kubelet,
                        number_services,
                        policy_size,
                        namespace,  # Pass namespace here
                    ),
                )
                thread.start()
                threads.append(thread)
            else:
                print(f"Skipping pod {pod} as it is not in Running state")

        # Run the kubectl command to create and replace the configmap (executed only once)
        configmap_command = f"kubectl create configmap opa-policy --from-file=policy.rego={policy} --dry-run=client -o yaml | kubectl replace -f -"
        subprocess.run(configmap_command, shell=True)

        # Set the start time and signal the event
        start_time_holder[0] = (
            datetime.utcnow().timestamp() * 1e9
        )  # Start time in nanoseconds
        start_event.set()

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        print(f"All pod monitoring processes have completed in iteration {i}")
        time.sleep(3)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Monitor OPA policies on Kubernetes Pods."
    )
    parser.add_argument("policy_1", type=str, help="Path to the first policy file.")
    parser.add_argument("policy_2", type=str, help="Path to the second policy file.")
    parser.add_argument("sync_kubelet", type=str, help="Sync Kubelet parameter.")
    parser.add_argument(
        "number_services", type=int, help="Number of services parameter."
    )
    parser.add_argument("policy_size", type=int, help="Policy size parameter.")
    parser.add_argument(
        "--namespace",
        type=str,
        default="default",
        help="Kubernetes namespace to monitor.",
    )
    parser.add_argument(
        "--log-identifier",
        type=str,
        default="REMOVE",
        help="Log identifier to monitor for.",
    )

    args = parser.parse_args()

    main(
        args.namespace,
        args.policy_1,
        args.policy_2,
        args.sync_kubelet,
        args.number_services,
        args.policy_size,
        args.log_identifier,
    )
