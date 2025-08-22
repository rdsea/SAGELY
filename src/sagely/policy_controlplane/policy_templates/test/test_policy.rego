package istio.authz_test

import rego.v1

import data.istio.authz

# In this test file:
# allow / allow, this defines the expected result (allow or deny) and runs the policy with given inputs.

# Test case for health check endpoint
test_admin_allow if {
	allow := data.istio.authz.allow with input as {"attributes": {
		"destination": {
			"address": {"socketAddress": {
				"address": "10.244.0.26",
				"portValue": 1338,
			}},
			"principal": "spiffe://cluster.local/ns/default/sa/default",
		},
		"metadataContext": {},
		"request": {
			"http": {
				"headers": {
					":authority": "context-management-service:1338",
					":method": "POST",
					":path": "/notify-leader-context",
					":scheme": "http",
					"accept": "*/*",
					"accept-encoding": "gzip, deflate",
					"content-length": "32",
					"content-type": "application/json",
					"traceparent": "00-46b8571b0142286d9baed1f8018a8147-5b7cfa24fa8faeef-01",
					"tracestate": "",
					"user-agent": "python-httpx/0.28.1",
					"x-envoy-attempt-count": "1",
					"x-forwarded-client-cert": "By=spiffe://cluster.local/ns/default/sa/default;Hash=4feccbd4f4e980410cb08aac5c361433d59efeb5453903ac6ab268c0f185ddf1;Subject=\"\";URI=spiffe://cluster.local/ns/default/sa/default",
					"x-forwarded-proto": "http",
					"x-request-id": "6d5332f5-01f7-9937-a2b1-c24f4960e700",
				},
				"host": "context-management-service:1338",
				"id": "2573117423648123836",
				"method": "POST",
				"path": "/notify-leader-context",
				"protocol": "HTTP/1.1",
				"scheme": "http",
			},
			"time": {
				"nanos": 411889000,
				"seconds": 1741070909,
			},
		},
		"routeMetadataContext": {},
		"source": {
			"address": {"socketAddress": {
				"address": "10.244.0.30",
				"portValue": 59598,
			}},
			"principal": "spiffe://cluster.local/ns/default/sa/default",
		},
	}}
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
