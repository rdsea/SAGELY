package istio.authz

import input.attributes.request.http as http_request
import input.parsed_path

# Default deny
default allow := false

# Allow health check endpoint (unconditionally)
allow if {
  http_request.method == "GET"
  http_request.path == ["health"]
}

allow if {
  roles_for_user[user_name][r]
  required_roles[r]
}

roles_for_user[user_name][r] if {
  r := user_roles[user_name][_]
}

required_roles[r] if {
  role_perms[r][_]
  perm := role_perms[r][_]
  perm.method == http_request.method
  perm.path == http_request.path
}

user_name := parsed if {
  [_, encoded] := split(http_request.headers.authorization, " ")
  [parsed, _] := split(base64url.decode(encoded), ":")
}

# Define user-role mapping
user_roles = {
  "alice": ["guest"],
  "bob": ["admin"],
  "charlie": ["admin"],
}

# Define role-permission mapping
role_perms = {
  "guest": [
    {"method": "POST", "path": "/preprocessing-gateway"},
    {"method": "POST", "path": "/notify-leader"},
    {"method": "GET", "path": "/get-counter"},
  ],
  "admin": [
    {"method": "POST", "path": "/preprocessing-gateway"},
    {"method": "POST", "path": "/notify-leader"},
    {"method": "GET", "path": "/heartbeat"},
    {"method": "POST", "path": "/update-counter"},
    {"method": "GET", "path": "/get-counter"},
    {"method": "GET", "path": "/get-command"},
  ],
  "user": [
    {"method": "POST", "path": "/preprocessing-gateway"},
    {"method": "POST", "path": "/notify-leader"},
    {"method": "POST", "path": "/heartbeat"},
    {"method": "POST", "path": "/update-counter"},
    {"method": "POST", "path": "/get-counter"},
    {"method": "POST", "path": "/get-command"},
  ],
}
