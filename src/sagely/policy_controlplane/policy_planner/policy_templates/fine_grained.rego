package istio.authz

import input.attributes.request.http as http_request

# Default deny
default allow := false

# Allow health check endpoint
allow if {
    http_request.method == "GET"
    http_request.path == ["health"]
    debug.log("Allowing health check")
}

# Allow if user has valid permissions
allow if {
    is_valid_user_and_allowed_action
}

# Authorization: Function to validate authorization header and check user permissions
is_valid_user_and_allowed_action {
    validate_auth_header
    debug.log("User name: " ++ _user_name)
    
    # Check user's group and role
    group_name := user_groups[_user_name].group
    role := user_groups[_user_name].role
    debug.log("User group: " ++ group_name)
    debug.log("User role: " ++ role)

    # Get permissions based on both group and role
    permissions := get_effective_permissions(group_name, role)
    
    # Check if requested action is allowed
    some permission in permissions
    debug.log("Checking permission for method: " ++ permission.method ++ ", path: " ++ permission.path)
    permission.method == http_request.method
    permission.path == http_request.path
}

# Function to validate the authorization header
validate_auth_header {
    debug.log("Authorization Header: " ++ http_request.headers.authorization)
    [_, encoded] := split(http_request.headers.authorization, " ")
    debug.log("Encoded part: " ++ encoded)
    [username, _] := split(base64url.decode(encoded), ":")
    _user_name = username
    debug.log("Decoded username: " ++ username)
}

_user_name := parsed if {
    [_, encoded] := split(http_request.headers.authorization, " ")
    [parsed, _] := split(base64url.decode(encoded), ":")
}

# 1. Zone-specific endpoints - Each group has access to their own zone paths
base_group_permissions = {
    "zone1_group": [
        {"method": "POST", "path": "/preprocessing-gateway"},
        {"method": "GET", "path": "/zone1/status"},
        {"method": "POST", "path": "/zone1/heartbeat"}
    ],
    "zone2_group": [
        {"method": "POST", "path": "/preprocessing-gateway"},
        {"method": "GET", "path": "/zone2/status"},
        {"method": "POST", "path": "/zone2/heartbeat"}
    ]
}

# 2. Role-specific operations - Different permissions based on role
role_permissions = {
    "leader": [
        {"method": "POST", "path": "/notify-leader"},
        {"method": "POST", "path": "/update-group-status"},
        {"method": "POST", "path": "/coordinate-tasks"},
        {"method": "POST", "path": "/manage-members"}
    ],
    "member": [
        {"method": "POST", "path": "/report-status"},
        {"method": "POST", "path": "/request-task"}
    ]
}

# Function to combine permissions based on group and role
get_effective_permissions(group_name, role) = permissions {
    base_perms := base_group_permissions[group_name]
    role_perms := role_permissions[role]
    permissions := array.concat(base_perms, role_perms)
}

# 3. Cross-zone operations - Special rules for cross-zone access
allow if {
    is_leader
    is_cross_zone_operation
}

# Helper to check if user is a leader
is_leader {
    user_groups[_user_name].role == "leader"
}

# Helper to check if operation is cross-zone
is_cross_zone_operation {
    startswith(http_request.path, "/cross-zone")
    http_request.method == "POST"
}

# 4. Emergency operations - Special access with additional token verification
allow if {
    is_emergency_operation
    is_leader
}

is_emergency_operation {
    http_request.path == "/emergency/override"
    http_request.method == "POST"
    http_request.headers["X-Emergency-Token"] == emergency_tokens[_user_name]
}

# 5. User-specific access control
user_groups = {
    "drone1": {"group": "zone1_group", "role": "leader"},
    "drone2": {"group": "zone1_group", "role": "member"},
    "drone3": {"group": "zone2_group", "role": "leader"},
    "drone4": {"group": "zone2_group", "role": "member"}
}


emergency_tokens = {
    "drone1": "emergency-token-1",
    "drone3": "emergency-token-2"
}