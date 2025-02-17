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
				"address": {"socketAddress": {
					"address": "10.244.0.12",
					"portValue": 1337,
				}},
				"principal": "spiffe://cluster.local/ns/default/sa/default",
			},
			"metadataContext": {},
			"request": {
				"http": {
					"headers": {
						":authority": "object-classification.test.com",
						":method": "POST",
						":path": "/update-counter",
						":scheme": "http",
						"accept": "*/*",
						"accept-encoding": "gzip, deflate",
						"authorization": "Basic 0:0",
						"content-length": "49",
						"content-type": "application/json",
						"traceparent": "00-d6c2ef5e6a74ab14aa546f6211a19665-1a92507e21e74039-01",
						"tracestate": "",
						"user-agent": "python-requests/2.32.3",
						"x-envoy-attempt-count": "1",
						"x-envoy-internal": "true",
						"x-forwarded-client-cert": "By=spiffe://cluster.local/ns/default/sa/default;Hash=d691631a80f0ced4ce5220576b7f1c5dd1ce6e4bed42a18c596c70bb68be616c;Subject=\"\";URI=spiffe://cluster.local/ns/istio-system/sa/istio-ingressgateway-service-account",
						"x-forwarded-for": "10.244.0.1",
						"x-forwarded-proto": "http",
						"x-request-id": "60d042ec-aa40-94dd-8d49-f58c2295fcd7",
					},
					"host": "object-classification.test.com",
					"id": "15955472530419881158",
					"method": "POST",
					"path": "/update-counter",
					"protocol": "HTTP/1.1",
					"scheme": "http",
				},
				"time": {
					"nanos": 629987000,
					"seconds": 1739796110,
				},
			},
			"routeMetadataContext": {},
			"source": {
				"address": {"socketAddress": {
					"address": "10.244.0.8",
					"portValue": 44388,
				}},
				"principal": "spiffe://cluster.local/ns/istio-system/sa/istio-ingressgateway-service-account",
			},
		},
		"parsed_body": null,
		"parsed_path": ["update-counter"],
		"parsed_query": {},
		"truncated_body": false,
		"version": {
			"encoding": "protojson",
			"ext_authz": "v3",
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
