from fastapi import FastAPI, Depends
from abc import ABC, abstractmethod
import logging
import requests
from policy_generator import generate_policy


app = FastAPI()


class PolicyPlanner(ABC):
    @abstractmethod
    def print(self):
        pass

    @abstractmethod
    def trigger_planner(self):
        pass

    @abstractmethod
    def service_discover(self):
        pass

    @abstractmethod
    def load_previous_policy(self) -> str:
        pass

    @abstractmethod
    def update_policy(self, previous_policy: str) -> str:
        """
        Generate new policy to be sent to policy coordinator
        """
        pass

    @abstractmethod
    def send_coordinator(self, new_policy: str):
        pass


class SagelyPolicyPlanner(PolicyPlanner):
    def print(self):
        pass

    def trigger_planner(self):
        previous_policy = self.load_previous_policy()
        new_policy = self.update_policy(previous_policy)
        self.send_coordinator(new_policy)

    def service_discover(self):
        pass

    def load_previous_policy(self) -> str:
        return ""

    def update_policy(self, previous_policy: str):
        return generate_policy(previous_policy)

    def send_coordinator(self, new_policy: str):
        response = requests.post(
            "http://policy-coordinator-service:6000/update_policy",
            json={"policy": new_policy},
        )
        if response.status_code != 200:
            logging.error(
                f"Updating new policy to coordinator failed with error code {response.status_code} and description:\n{response.text}"
            )
        else:
            logging.info("Updating new policy to coordinator successfully")


def get_handler() -> PolicyPlanner:
    handler = SagelyPolicyPlanner()
    return handler


@app.get("/print")
def api_print(handler: PolicyPlanner = Depends(get_handler)):
    return handler.print()


@app.post("/trigger_planner")
def api_trigger_planner(handler: PolicyPlanner = Depends(get_handler)):
    return handler.trigger_planner()
