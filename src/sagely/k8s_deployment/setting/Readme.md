# testing area
- NOTE: Flow of the setting 
1. minikube
2. Istio
3. OPA
4. application
5. Jaeger
6. run again OPA 
```bash
./enable-external-authorization.sh

kubectl label namespace default opa-istio-injection=enabled
```
## add-ons area
```bash
minikube addons enable ingress

minikube addons enable metallb

k apply -f config-metallb.yml
```

## Istio
```bash
istioctl install --set profile=default -y

kubectl label namespace default istio-injection=enabled

kubectl apply -f jaeger-istio.yml
```

## OPA 
```bash
# cd policy_update
#policy_update/istio-opa/opa-controller-sidecar.yml
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/opa-envoy-plugin/main/examples/istio/quick_start.yaml

./enable-external-authorization.sh

kubectl label namespace default opa-istio-injection=enabled
```

## application

```bash
kubectl apply -f https://raw.githubusercontent.com/istio/istio/master/samples/bookinfo/platform/kube/bookinfo.yaml

kubectl apply -f https://raw.githubusercontent.com/istio/istio/master/samples/bookinfo/networking/bookinfo-gateway.yaml
```

## Jaeger

```bash
# cd monitoring 
#kubectl apply -f jaeger-istio.yml

istioctl install -f tracing.yml --skip-confirmation

kubectl apply -f enable_tracing.yml
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
for i in $(seq 1 100); do curl -s -o /dev/null "http://$SERVICE_HOST/productpage"; done
```
