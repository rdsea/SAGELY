#!/bin/bash
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
#
#
set -e

NAMESPACE="istio-system"
CONFIGMAP_NAME="istio"
EXTERNAL_AUTH_PROVIDER_NAME="opa-ext-authz-grpc"
SERVICE_NAME="opa-ext-authz-grpc.local"
PORT=9191

# Fetch the existing ConfigMap and convert it to JSON
kubectl get configmap -n $NAMESPACE $CONFIGMAP_NAME -o json >istio-configmap.json

# Extract the 'mesh' section
MESH_DATA=$(jq -r '.data.mesh' istio-configmap.json)

# Add the external provider to the 'mesh' configuration
UPDATED_MESH_DATA=$(
  echo "$MESH_DATA" |
    awk 'BEGIN {FS=OFS="\n"} 
  { 
    found=0
    for (i=1; i<=NF; ++i) {
      print $i
      if ($i ~ /extensionProviders:/) {
        found=1
        print "    - name: '"$EXTERNAL_AUTH_PROVIDER_NAME"'"
        print "      envoyExtAuthzGrpc:"
        print "        service: '"$SERVICE_NAME"'"
        print "        port: '"$PORT"'"
      }
    }
    if (found == 0) {
      print "extensionProviders:"
      print "  - name: '"$EXTERNAL_AUTH_PROVIDER_NAME"'"
      print "    envoyExtAuthzGrpc:"
      print "      service: '"$SERVICE_NAME"'"
      print "      port: '"$PORT"'"
    }
  }'
)

# Update the mesh section in the original JSON
UPDATED_CONFIGMAP=$(jq --arg updated_mesh "$UPDATED_MESH_DATA" '.data.mesh = $updated_mesh' istio-configmap.json)

# Save the updated JSON to a file
echo "$UPDATED_CONFIGMAP" >updated-istio-configmap.json

# Apply the updated ConfigMap
kubectl apply -f updated-istio-configmap.json

# Clean up
rm istio-configmap.json updated-istio-configmap.json

echo "Istio ConfigMap has been updated with the external authorizer."
