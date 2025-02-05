# Steps for running

1. Minikube start with loadbalancer
  - metallb
    - apply config metallb
  - ingress
  
2. Istio
  - default profile
  - apply virtualServices, gateway, and destination-rules
  - label enable sidecar injection

3. opa
  - apply the quick configuration
  - run script to enable external authorization
  - label enable sidecar injection

4. application
  - run via tilt
