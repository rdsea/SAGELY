# Policy Change Management Service

This service provides a centralized mechanism for managing and distributing OPA (Open Policy Agent) policies to various targets, including Kubernetes clusters and UAVs (drones).

## Overview

The Policy Change Management Service is a FastAPI application that receives policy change requests and executes them. It supports updating policies in Kubernetes ConfigMaps and sending policies to UAVs using MAVLink FTP. The service is designed to be extensible, allowing for the addition of new target types.

## Features

-   **Centralized Policy Management**: A single service to manage and distribute OPA policies.
-   **Multiple Target Types**: Supports updating policies in Kubernetes clusters and sending them to UAVs.
-   **Extensible Architecture**: Easily add support for new target types.
-   **Containerized**: Can be run as a Docker container.
-   **Latency Measurement**: Includes scripts to measure the latency of policy updates.

## Architecture

The service consists of the following components:

-   **Policy Change Management Service**: A FastAPI application that receives policy change requests and orchestrates the updates.
-   **Execution Scripts**: A collection of Python scripts that perform the actual policy updates on the different targets.
-   **OPA Policies**: OPA policies written in Rego.
-   **Configuration**: YAML files for configuring the service and the targets.

## Getting Started

### Prerequisites

-   Python 3.8+
-   Docker
-   Kubernetes cluster (optional, for Kubernetes integration)
-   PX4 Autopilot (optional, for UAV integration)

### Running the Service

1.  Start the FastAPI application:
    ```bash
    ./run_server.sh
    ```
2.  The service will be available at `http://localhost:1341`.

### Building and Running with Docker

1.  Build the Docker image:
    ```bash
    docker build -t policy-change-management .
    ```
2.  Run the Docker container:
    ```bash
    docker run -p 1341:1341 policy-change-management
    ```

## Usage

To execute a policy change, send a POST request to the `/execute_change` endpoint with a list of execution steps.

**Example:**

```json
[
    {
        "action": "kubectl apply -f deployment.yaml",
        "details": {}
    }
]
```

## Scripts

The `src` directory contains several Python scripts for interacting with the service and the targets:

-   `policy_change_management.py`: The core FastAPI application.
-   `apply_policy_cluster.py`: Updates an OPA policy ConfigMap in a Kubernetes cluster.
-   `send_FTP_px4.py`: Sends a policy file to a UAV using MAVLink FTP.
-   `send_request_normal.py`: Sends a policy to an OPA server.
-   `send_request_px4.py`: Sends policy data to a PX4 Autopilot using MAVLink.
-   `send_request_service.py`: A FastAPI service for sending policies to OPA servers.
