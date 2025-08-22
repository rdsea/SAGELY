curl -L https://istio.io/downloadIstio | sh -
cd istio-1.25.0 || exit
export PATH=$PWD/bin:$PATH

istioctl install --set profile=default -y
kubectl label namespace default istio-injection=enabled
kubectl label namespace default opa-istio-injection="enabled"
cd ..

# OPA admission
kubectl apply -f src/holistic_policy/k8s_deployment/istio-opa/opa_controller.yml
kubectl apply -f src/holistic_policy/k8s_deployment/istio-opa/opa_authz.yml
kubectl apply -f src/holistic_policy/k8s_deployment/istio-opa/opa_config.yml

# enable external provider: jaeger and OPA
istioctl install -f src/holistic_policy/k8s_deployment/monitoring/external_provider.yml --skip-confirmation
kubectl apply -f src/holistic_policy/k8s_deployment/monitoring/enable_tracing.yml
kubectl apply -f src/holistic_policy/k8s_deployment/monitoring/prometheus.yml

# deploy JAEGER
kubectl apply -f src/holistic_policy/k8s_deployment/monitoring/jaeger_istio.yml

# Apply routing rule
kubectl apply -f src/holistic_policy/k8s_deployment/policy_deployment/platform_context.yml
kubectl apply -f src/holistic_policy/k8s_deployment/policy_deployment/service_discovery.yml
kubectl apply -f src/holistic_policy/k8s_deployment/policy_deployment/context_management.yml

kubectl apply -f src/holistic_policy/k8s_deployment/istio/application_gateway.yml
kubectl apply -f src/holistic_policy/k8s_deployment/istio/virtual_services.yml
kubectl apply -f src/holistic_policy/k8s_deployment/istio/destination_rules.yml
