# Steps to execute the OPA 

1. create external connection
> ./enable-external-authorization.sh

2. apply configuration
> kubectl apply -f opa-controller-sidecar.yml

3. enable sidecar injection
> kubectl label namespace default opa-istio-injection=enabled

# debug

```bash
kubectl describe pod/<pod namne>
# this one returns potential containers inside the pod

kubectl logs <po name> -c <container in the pod> -n <namespace> --tail=-1
# example:   kubectl logs productpage-v1-d49bb79b4-tjd5v -c opa-istio -n default --tail=-1
```
