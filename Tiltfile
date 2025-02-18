docker_build('service_discovery', 'src/holistic_policy', 
   dockerfile="src/holistic_policy/service_discovery/Dockerfile",
   only=["service_discovery"]
)

docker_build('rdsea/preprocessing', 'applications/object_classification/src', 
   dockerfile="applications/object_classification/src/preprocessing/Dockerfile",
   only=["preprocessing", "util"]
)

docker_build('rdsea/ensemble', 'applications/object_classification/src', 
   dockerfile="applications/object_classification/src/ensemble/Dockerfile",
   only=["ensemble", "util"]
)

docker_build('rdsea/inference:cpu', 'applications/object_classification/src', 
   dockerfile="applications/object_classification/src/inference/Dockerfile.cpu", 
   only=["inference", "util"]
   )


print("Enabling Ingress and MetalLB addons...")
local("minikube addons enable ingress")
local("minikube addons enable metallb")

print("Configuring MetalLB...")
minikube_ip = str(local("minikube ip")).strip()
print("Minikube IP: " + minikube_ip)

# Extract network base from IP to create a network range
minikube_network_prefix = ".".join(minikube_ip.split(".")[:3])
minikube_network_range = minikube_ip + "-{0}.255".format(minikube_network_prefix)

print(minikube_network_range)

#Construct the MetalLB ConfigMap content directly in the shell command
metallb_config = """
apiVersion: v1
kind: ConfigMap
metadata:
  namespace: metallb-system
  name: config
data:
  config: |
    address-pools:
    - name: default
      protocol: layer2
      addresses:
      - {network_range}
""".format(network_range=minikube_network_range)

# Using a shell command to write config and apply it directly
local('echo "{content}" | kubectl apply -f -'.format(content=metallb_config))

# ISTIO
# install istio default profile and enable
local("istioctl install --set profile=default -y")
local("kubectl label namespace default istio-injection=enabled")

# deploy JAEGER
k8s_yaml('src/holistic_policy/k8s_deployment/monitoring/jaeger_istio.yml')

# OPA admission
k8s_yaml('src/holistic_policy/k8s_deployment/istio-opa/opa_controller_sidecar.yml')

# enable external provider: jaeger and OPA
local("istioctl install -f src/holistic_policy/k8s_deployment/monitoring/external_provider_tracing_opa.yml --skip-confirmation")
k8s_yaml('src/holistic_policy/k8s_deployment/monitoring/enable_tracing.yml') # enable tracing

# enable opa sidecar
local("kubectl label namespace default opa-istio-injection=enabled")

# application
k8s_yaml('applications/object_classification/src/deployment/preprocessing.yml')
k8s_yaml('applications/object_classification/src/deployment/ensemble.yml')
k8s_yaml('applications/object_classification/src/deployment/MobileNetV2.yml')
k8s_yaml('applications/object_classification/src/deployment/EfficientNetB0.yml')

# src
k8s_yaml('src/holistic_policy/k8s_deployment/policy_deployment/service_discovery.yml')

#k8s_yaml('object_classification/src/deployment/jaeger.yml')

#istio routing and gateway
k8s_yaml('src/holistic_policy/k8s_deployment/istio/application_gateway.yml')
k8s_yaml('src/holistic_policy/k8s_deployment/istio/virtual_services.yml')
k8s_yaml('src/holistic_policy/k8s_deployment/istio/destination_rules.yml')

k8s_resource('jaeger', port_forwards=16686)
