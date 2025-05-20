from diagrams import Cluster, Diagram
from diagrams.gcp.database import BigTable
from diagrams.gcp.ml import AIPlatform
from diagrams.k8s.compute import Deployment
from diagrams.onprem.network import Nginx
from diagrams.onprem.queue import RabbitMQ
from diagrams.generic.os import Raspbian
from diagrams.generic.compute import Rack
from diagrams.generic.network import Router

with Diagram("ML pipeline", show=False):
    with Cluster("Edge"):
        preprocessing = Deployment("Preprocessing")
        inference = Deployment("Inference")
        message_queue_1 = RabbitMQ("Message Queue 1")
        message_queue_2 = RabbitMQ("Message Queue 2")
        gateway = Nginx("Gateway")
    with Cluster("Cloud"):
        database = BigTable("Inference Result")
        cloud_inference = AIPlatform("Cloud Inference")

    with Cluster("IoT"):
        for i in range(1, 4):
            raspbian = Raspbian(f"Raspberry Pi {i}")
            raspbian >> gateway
    for i in range(1, 3):
        with Cluster(f"External provider {i}"):
            router = Router("Router")
            for i in range(1, 4):
                rack = Rack(f"Rack {i}")
                router >> rack
            message_queue_1 >> router
    (
        gateway
        >> preprocessing
        >> message_queue_1
        >> inference
        >> message_queue_2
        >> database
    )
    message_queue_1 >> cloud_inference >> database
