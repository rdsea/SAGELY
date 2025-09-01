package envoy.authz
import rego.v1
import input.attributes.request.http

default allow := false
