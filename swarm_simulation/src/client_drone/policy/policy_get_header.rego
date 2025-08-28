package envoy.authz

default allow = false

allow {
  input.attributes.request.http.headers["x-allow"] == "1"
}

######################
#  Testing
##########################
# curl -sS localhost:5201/clusters | grep -A3 opa_ext_authz
# Request without header (403 if you used the gated policy)
# curl -i http://localhost:5200/
# Request with header (200 OK)
# curl -i -H "x-allow: 1" http://localhost:5200/

