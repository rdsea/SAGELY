# What do you can do?

[this link](https://istio.io/latest/docs/tasks/observability/distributed-tracing/jaeger/)

# testing area

1. minikube
2. Istio and enable label
3. deploy [Jaeger](https://istio.io/latest/docs/tasks/observability/distributed-tracing/jaeger/) and OPA yml
4. Apply external provider for Jaeger and OPA
5. enable label for OPA and apply [tracing](https://istio.io/latest/docs/tasks/observability/telemetry/) (this file allow to config with various sampling rate and other tags)
6. application

```bash
minikube delete; minikube start --cpus max --memory max --addons=ingress,metallb; k apply -f config-metallb.yml

# cd istio
istioctl install --set profile=default -y; kubectl label namespace default istio-injection=enabled
kubectl apply -f jaeger-istio.yml

# cd policy_update/istio-opa
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/opa-envoy-plugin/main/examples/istio/quick_start.yaml

# cd monitoring
istioctl install -f external-provider-tracing-opa.yml --skip-confirmation
# apply
kubectl apply -f enable_tracing.yml
kubectl label namespace default opa-istio-injection=enabled

# application
# bookinfo for this example
kubectl apply -f https://raw.githubusercontent.com/istio/istio/master/samples/bookinfo/platform/kube/bookinfo.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/master/samples/bookinfo/networking/bookinfo-gateway.yaml
```

# Testing

## OPA

```bash
export SERVICE_HOST=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

curl --user alice:password -i http://$SERVICE_HOST/productpage

curl --user alice:password -i http://$SERVICE_HOST/api/v1/products
```

## Jaeger

```bash
for i in $(seq 1 100); do curl --user alice:password -s -o /dev/null "http://$SERVICE_HOST/productpage"; done
```
