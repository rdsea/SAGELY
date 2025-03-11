import os


def generate_rego_file(filename, size_kb):
    base_rego = """package istio.authz

import input.attributes.request.http as http_request
import input.parsed_path

default allow := false

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
	base_path := trim_query(http_request.path)
	path_matches(base_path, perm.path)
}

trim_query(path_with_query) := base_path if {
	paths := split(path_with_query, "?")
	base_path := paths[0]
}

path_matches(request_path, policy_path) if {
	regex.match(policy_path, request_path)
}

user_roles := {
"""

    role_perms_str = "role_perms := {\n"
    user_roles_str = ""
    num_users = size_kb * 10  # Adjust based on testing
    num_perms = size_kb * 15  # Adjust based on testing

    for i in range(num_users):
        user_roles_str += f'    "{i}": ["role{i%10}"],\n'

    for i in range(num_perms):
        role_perms_str += (
            f'    "role{i%10}": [{{"method": "GET", "path": "/path{i}"}}],\n'
        )

    role_perms_str += "}\n"
    user_roles_str += "}\n"

    rego_content = base_rego + user_roles_str + "\n" + role_perms_str

    with open(filename, "w") as f:
        f.write(rego_content)

    print(f"Generated {filename} with size {os.path.getsize(filename) / 1024:.2f} KB")


# Generate 30KB and 300KB Rego files
generate_rego_file("rego_30kb.rego", 30)
generate_rego_file("rego_300kb.rego", 300)
