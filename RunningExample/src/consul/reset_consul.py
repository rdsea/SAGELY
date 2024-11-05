import argparse

from rohe.common import rohe_utils
from rohe.service_registry.consul import ConsulClient

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Argument for Ingestion Service")
    parser.add_argument(
        "--conf",
        type=str,
        help="specify configuration file path",
        default="resetConsul.yaml",
    )
    parser.add_argument("--id", type=str, help="specify service endpoint", default="")

    args = parser.parse_args()
    config_file = args.conf
    config = rohe_utils.load_config(file_path=config_file)
    assert config is not None
    consul_client = ConsulClient(config=config["service_registry"]["consul_config"])
    for service in config["service"]:
        instance_list = consul_client.get_all_service_instances(service)
        for instance in instance_list:
            result = consul_client.service_deregister(instance["ID"])
            if result:
                print(
                    "Service {}, instance {} deregister success".format(
                        service, instance["ID"]
                    )
                )
