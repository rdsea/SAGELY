package envoy.authz

default allow = false

allow if {
    input.attributes.request.http.method == "GET"
    input.attributes.request.http.path == "/preprocessing"
    input.attributes.request.http.headers.authorization == "Basic drone_0:0"

}

