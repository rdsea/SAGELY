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

	#perm.path == http_request.path
	# Ignore query parameters by considering only the base path
	base_path := trim_query(http_request.path)
	base_path == perm.path
}

#user_name := parsed if {
#  [_, encoded] := split(http_request.headers.authorization, " ")
#  [parsed, _] := split(base64url.decode(encoded), ":")
#}

# parse user_name, password
user_name := parsed if {
	[_, encoded] := split(http_request.headers.authorization, " ")
	[parsed, _] := split(encoded, ":")
	print("username: hihop", parsed, "\n")
}

# simplify password with group_id
password := parsed if {
	[_, encoded] := split(http_request.headers.authorization, " ")
	[_, parsed] := split(encoded, ":")
	print("passowrd: ", parsed, "\n")
}

# Trim query parameters from path
trim_query(path_with_query) := base_path if {
	# Fallback to the full path if there's no query parameter
	paths := split(path_with_query, "?")
	base_path := paths[0]
}

# Define user-role mapping
user_roles := {
	"0": ["admin"],
	"1": ["admin"],
	"2": ["admin"],
	"3": ["user"],
	"4": ["user"],
	"5": ["user"],
	"6": ["guest"],
	"7": ["guest"],
}

# Define role-permission mapping
role_perms := {
	"admin": [
		# service_discovery
		{"method": "POST", "path": "/notify-leader"},
		{"method": "POST", "path": "/heartbeat"},
		{"method": "POST", "path": "/update-counter"},
		{"method": "GET", "path": "/get-counter"},
		{"method": "GET", "path": "/get-command"},
		# application
		{"method": "POST", "path": "/preprocessing/"}, # Include the preprocessing endpoint
		{"method": "POST", "path": "/ensemble_service/"}, # Include the preprocessing endpoint
		{"method": "POST", "path": "/inference"}, # Include the preprocessing endpoint
	],
	"guest": [
		{"method": "POST", "path": "/preprocessing-gateway"},
		{"method": "POST", "path": "/notify-leader"},
		{"method": "GET", "path": "/get-counter"},
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
