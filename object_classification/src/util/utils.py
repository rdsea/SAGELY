from __future__ import annotations

import json
import socket

import yaml
from consul import ConsulClient
import logging


def get_local_ip():
    try:
        # The following line creates a socket to connect to an external site
        # The IP address returned is the one of the network interface used for the connection
        # '8.8.8.8' is used here as it's a public DNS server by Google
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        return "Unable to get IP: " + str(e)


def load_config(file_path: str) -> dict | None:
    """
    file_path: file path to load config
    """
    try:
        if "json" in file_path:
            with open(file_path) as f:
                return json.load(f)
        if ("yaml" in file_path) or ("yml" in file_path):
            with open(file_path) as f:
                return yaml.safe_load(f)
        else:
            return None
    except yaml.YAMLError as exc:
        print(exc)


def handle_service_query(
    consul_client: ConsulClient, service_name, query_type, tags: list[str] | None = None
):
    try:
        if query_type == "all":
            return consul_client.get_all_service_instances(service_name, tags)

        if query_type == "one":
            return consul_client.get_n_random_service_instances(service_name, tags, n=1)

        if query_type == "quorum":
            return consul_client.get_quorum_service_instances(service_name, tags)

        logging.error(f"Invalid query type: {query_type}")
        return None
    except Exception as e:
        logging.error(f"Error in handle_service_query: {e}")
        return None
