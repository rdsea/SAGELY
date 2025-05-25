# IFIP Performance experiments

## Cilium

- If using k3s, remember to set up cilium with this as k3s default podCIDR is 10.42.0.0/16

```bash
cilium install --version 1.17.4 --set=ipam.operator.clusterPoolIPv4PodCIDRList="10.42.0.0/16"
```

- Remember to set up the gateway API for the k8s cluster first [source](https://gateway-api.sigs.k8s.io/guides/):

```bash
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.3.0/standard-install.yaml
```

- To use cilium gateway, try to follow the [guide](https://docs.cilium.io/en/stable/network/servicemesh/gateway-api/gateway-api/), especially the part about prerequisite

- Install metallb for getting the external ip for gateway

```bash
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.14.9/config/manifests/metallb-native.yaml
kubectl apply -f applications/object_classification/src/deployment/metallb_config.yml
```
