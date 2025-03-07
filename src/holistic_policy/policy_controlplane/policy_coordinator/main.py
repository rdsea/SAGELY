from abc import ABC, abstractmethod

from pydantic import BaseModel
from fastapi import Depends, FastAPI
from kubernetes import client, config
from kubernetes.client.rest import ApiException

app = FastAPI()


class PolicyCoordinator(ABC):
    @abstractmethod
    def print(self):
        pass

    @abstractmethod
    def update_policy(self, new_policy: str):
        pass


class SagelyPolicyPlanner(PolicyCoordinator):
    def print(self):
        pass

    def update_policy(self, new_policy: str):
        try:
            config.load_kube_config()

            v1 = client.CoreV1Api()

            configmap_name = "opa-policy"
            namespace = "default"

            configmap = client.V1ConfigMap(
                api_version="v1",
                kind="ConfigMap",
                metadata=client.V1ObjectMeta(name=configmap_name),
                data={"policy.rego": new_policy},
            )

            try:
                v1.replace_namespaced_config_map(
                    name=configmap_name, namespace=namespace, body=configmap
                )
                print("ConfigMap 'opa-policy' updated successfully.")
            except ApiException as e:
                if e.status == 404:
                    v1.create_namespaced_config_map(namespace=namespace, body=configmap)
                    print(f"ConfigMap '{configmap_name}' created successfully.")
                else:
                    print(f"Error updating ConfigMap: {e}")

        except ApiException as e:
            print(f"Exception when interacting with Kubernetes: {e}")


def get_handler() -> PolicyCoordinator:
    handler = SagelyPolicyPlanner()
    return handler


class NewPolicy(BaseModel):
    policy: str


@app.get("/print")
def api_print(handler: PolicyCoordinator = Depends(get_handler)):
    return handler.print()


@app.put("/update_policy")
def api_update_policy(
    new_policy: NewPolicy, handler: PolicyCoordinator = Depends(get_handler)
):
    return handler.update_policy(new_policy.policy)
