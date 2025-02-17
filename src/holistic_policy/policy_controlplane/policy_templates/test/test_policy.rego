package istio.authz_test

import rego.v1

import data.istio.authz

# In this test file:
# allow / allow, this defines the expected result (allow or deny) and runs the policy with given inputs.

# Test case for health check endpoint
test_admin_allow if {
	allow := data.istio.authz.allow with input as {
  "attributes": {
      "destination": {
        "address": {
          "socketAddress": {
            "address": "10.244.0.39",
            "portValue": 1337
          }
        },
        "principal": "spiffe://cluster.local/ns/default/sa/default"
      },
      "metadataContext": {},
      "request": {
        "http": {
          "headers": {
            ":authority": "object-classification.test.com",
            ":method": "POST",
            ":path": "/heartbeat",
            ":scheme": "http",
            "accept": "*/*",
            "accept-encoding": "gzip, deflate",
            "authorization": "Basic 0:0",
            "content-length": "35",
            "content-type": "application/json",
            "traceparent": "00-166767fd8d29ab65f9095a92b59d98af-bcfb3ec3fcdf2fd8-01",
            "tracestate": "",
            "user-agent": "python-requests/2.32.3",
            "x-envoy-attempt-count": "1",
            "x-envoy-internal": "true",
            "x-forwarded-client-cert": "By=spiffe://cluster.local/ns/default/sa/default;Hash=d691631a80f0ced4ce5220576b7f1c5dd1ce6e4bed42a18c596c70bb68be616c;Subject=\"\";URI=spiffe://cluster.local/ns/istio-system/sa/istio-ingressgateway-service-account",
            "x-forwarded-for": "10.244.0.1",
            "x-forwarded-proto": "http",
            "x-request-id": "67f2084d-440c-9b0c-9644-57cc88c9f165"
          },
          "host": "object-classification.test.com",
          "id": "8227617712332952062",
          "method": "POST",
          "path": "/heartbeat",
          "protocol": "HTTP/1.1",
          "scheme": "http"
        },
        "time": {
          "nanos": 525045000,
          "seconds": 1739811759
        }
      },
      "routeMetadataContext": {},
      "source": {
        "address": {
          "socketAddress": {
            "address": "10.244.0.8",
            "portValue": 49244
          }
        },
        "principal": "spiffe://cluster.local/ns/istio-system/sa/istio-ingressgateway-service-account"
      }
    },
	}
	allow == true
}

#
# test_get_anonymous_denied if {
# 	not authz.allow with input as {"path": ["users"], "method": "GET"}
# }
#
# test_get_user_allowed if {
# 	authz.allow with input as {"path": ["users", "bob"], "method": "GET", "user_id": "bob"}
# }
#
# test_get_another_user_denied if {
# 	not authz.allow with input as {"path": ["users", "bob"], "method": "GET", "user_id": "alice"}
# }
