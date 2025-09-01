
package istio.authz

# Be maximally compatible with OPA versions used in Istio
default allow = false

# Allow health
allow {
  input.attributes.request.http.method == "GET"
  input.attributes.request.http.path == "/health"
}

# Role-based allow
allow {
  some r
  u := user_name
  r := roles_for_user[u][_]
  required_for_request(r)
}

required_for_request(r) {
  some perm
  perm := role_perms[r][_]
  perm.method == input.attributes.request.http.method
  norm_path(input.attributes.request.http.path) == norm_path(perm.path)
}

# Normalize "/a?x=y" -> "/a", remove trailing slash
norm_path(p) = out {
  no_q := split(p, "?")[0]
  out := trim_suffix(no_q, "/")
}

# ---- Authorization parsing ----
# Accept either "Basic user:pass" (non-RFC) or "Basic <base64(user:pass)>"
user_name = u {
  hdr := input.attributes.request.http.headers.authorization
  startswith(hdr, "Basic ")
  rest := trim_prefix(hdr, "Basic ")
  contains(rest, ":")
  u := split(rest, ":")[0]
} else = u {
  hdr := input.attributes.request.http.headers.authorization
  startswith(hdr, "Basic ")
  rest := trim_prefix(hdr, "Basic ")
  dec := base64.decode(rest)
  u := split(dec, ":")[0]
}

# ---- Mappings ----
roles_for_user := {
  "drone_0": ["admin"],
  "drone_1": ["admin"],
  "drone_2": ["admin"],
  "0": ["admin"],
  "1": ["admin"],
  "2": ["admin"],
  "3": ["user"],
  "4": ["user"],
  "5": ["user"],
  "6": ["guest"],
  "7": ["guest"],
}

role_perms := {
  "admin": [
    {"method": "POST", "path": "/notify-leader"},
    {"method": "POST", "path": "/heartbeat"},
    {"method": "POST", "path": "/update-counter"},
    {"method": "GET",  "path": "/get-counter"},
    {"method": "GET",  "path": "/get-command"},
    {"method": "POST", "path": "/preprocessing"},
    {"method": "POST", "path": "/ensemble_service"},  # <- no trailing slash
    {"method": "POST", "path": "/inference"},
  ],
  "user": [
    {"method": "POST", "path": "/preprocessing-gateway"},
    {"method": "POST", "path": "/notify-leader"},
    {"method": "POST", "path": "/heartbeat"},
    {"method": "POST", "path": "/update-counter"},
    {"method": "POST", "path": "/get-counter"},
    {"method": "POST", "path": "/get-command"},
  ],
  "guest": [
    {"method": "POST", "path": "/preprocessing-gateway"},
    {"method": "POST", "path": "/notify-leader"},
    {"method": "GET",  "path": "/get-counter"},
  ],
}

