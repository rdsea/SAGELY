# policy-update

Describe your project here.
rye add opal-client

## Edit CM from Istio in Kubernetes
```bash
# Add the following to the mesh config to enable external authorization:
# mesh: |-
#   # ADD THIS HERE
# extensionProviders:
# - name: opa-ext-authz-grpc
#   envoyExtAuthzGrpc:
#     service: opa-ext-authz-grpc.local
#     port: 9191
#   # END
#   defaultConfig:
#     discoveryAddress: istiod.istio-system.svc:15012
```


