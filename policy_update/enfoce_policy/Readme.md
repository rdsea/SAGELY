# What I have done? for automatically

## Setting OPA check change
- utilize "--watch" which allow OPA to check the change from the predefined directories 

```yaml asking OPA sidecar frequently check policy.rego from opa-controller-sidecar.yml
    opa_container = {
      "image": "openpolicyagent/opa:latest-istio",
      "name": "opa-istio",
      "args": [
        "run",
        "--server",
        "--config-file=/config/config.yaml",
        "--addr=localhost:8181",
        "--diagnostic-addr=0.0.0.0:8282",
        "--watch",
        "/policy/policy.rego",
      ],
```

```yaml asking OPA controller frequently check inject.rego in deployment of admission-controller
    spec:
      containers:
        - image: openpolicyagent/opa:latest
          name: opa
          ports:
            - containerPort: 8443
          args:
            - "run"
            - "--server"
            - "--tls-cert-file=/certs/tls.crt"
            - "--tls-private-key-file=/certs/tls.key"
            - "--addr=0.0.0.0:8443"
            - "--watch" # Add this flag to enable watching and spread the new configuration to sidecars -- need to check more they consume data and policies together
            - "/policies/inject.rego"
            #- "/policies/"
```

## Applying the new policies
- apply the change is from the kubernete if the new policy called newPoclicy.rego or can apply directly configmap-new.yml

> kubectl create configmap opa-policy --from-file=policy.rego=newPolicy.rego  --dry-run=client -o yaml | kubectl replace -f -

OR
> kubectl apply -f configmap-new.yml


# What I can do for manual?

## At each service the policy.rego can be changed as below:
- access to a pod for example 
> k exec -it gateway-787cb7f849-k8scd -- /bin/bash
- install curl for communicate with other services
- get current policies from 
> curl -X GET http://localhost:8181/v1/policies
- apply the change of policies, the new rego policy called newPolicy.rego
> curl -X PUT -H "Content-Type: text/plain" --data-binary @newPolicy.rego http://localhost:8181/v1/policies/newPolicy




