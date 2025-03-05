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

# MAIN
required_roles[r] if {
	role_perms[r][_]
	perm := role_perms[r][_]
	perm.method == http_request.method

	#perm.path == http_request.path

	# Ignore query parameters by considering only the base path
	base_path := trim_query(http_request.path)

	# check base_path with correctly permisison.path
	#base_path == perm.path

	# check the base_path with permisison.path including regex
