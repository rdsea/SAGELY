# Plan B: UAV identity and registry service

Date: 2026-11-05 · Status: proposal
Baseline: [current status](20261105-swarm-status.md) · Related: [Plan A: GCS control](20261105-plan-gcs-control.md)

In this plan, "UAV" and "drone" mean the same thing.

## 1. Problem

Today a drone's identity comes from an IP range and a loop counter. It is then
copied by hand into six places (I1), and the copies already drift: drone_104
is missing from `client_config.yaml`, and the edge policy only knows
drone_101–103. Other problems follow from this:

- There is no authentication. A drone's name alone gives access (I2).
- A group change is not recorded centrally (I3).
- Presence is kept only in memory, and only for group leaders (I4).
- IDs collide between batches (G6). Plan A needs a unique sysid per drone.
- OPA does not check the platform endpoints (S2).
- Every drone runs its own etcd (N1).

## 2. Goals and non-goals

Goals:

1. One source of truth for each drone's identity. Everything else is generated
   from it or looked up.
2. Drones can join and leave at runtime, without anyone editing files.
3. The sysid, the ROS 2 namespace and the Gazebo model name are unique across
   batches and restarts.
4. Each drone proves who it is with a short-lived signed token, not with
   `Basic <name>:<group>`.
5. Policies read identity from OPA data. A new drone is a data change, not a
   Rego change.
6. Presence (active or lost) feeds context management.

Non-goals for the first version:

- Hardware attestation (TPM) and a full PKI.
- Running SPIRE. The IDs follow the SPIFFE format, so SPIRE can be added later.
- Several swarms or tenants.
- Replacing Istio mTLS between edge services.

## 3. Four separate concerns

| Concern | Lifetime | Example | Owner |
|---|---|---|---|
| Identity | until retired | `drone_101`, `spiffe://sagely/uav/drone_101`, public key | registry |
| Allocation | while registered | sysid 101, DDS namespace, Gazebo name, group | registry |
| Credential | minutes | access token (JWT, ES256, 15 min) | registry issues it; edge and drones check it |
| Presence | seconds | lease, `last_seen`, active or lost | registry, fed by drones or the GCS |

These four must stay separate:
- A lost drone keeps its identity and its sysid.
- An expired token does not mean the drone is lost.
- A group change does not create a new identity.

Keep `drone_<n>` as the ID, because the code, the logs and the papers already
use it.

## 4. Data model (SQLite)

```sql
CREATE TABLE uav (
  uav_id       TEXT PRIMARY KEY,          -- "drone_101"
  spiffe_id    TEXT UNIQUE NOT NULL,      -- "spiffe://sagely/uav/drone_101"
  sysid        INTEGER UNIQUE NOT NULL,   -- 1..239, see Plan A D1
  model        TEXT,                      -- "gz_x500"
  group_id     TEXT NOT NULL,             -- "0"
  roles        TEXT NOT NULL,             -- JSON list, e.g. ["drone"]
  capabilities TEXT,                      -- JSON list, e.g. ["camera"]
  public_key   TEXT NOT NULL,             -- JWK of the drone's ES256 key
  state        TEXT NOT NULL,             -- provisioned | active | lost | retired
  policy_rev   INTEGER,                   -- last active revision the drone reported
  created_at   TEXT, updated_at TEXT, last_seen_at TEXT
);

CREATE TABLE join_token (
  token_hash TEXT PRIMARY KEY,            -- SHA-256; never store the token itself
  name_hint  TEXT, group_id TEXT,
  expires_at TEXT, used_at TEXT
);

CREATE TABLE event (                      -- audit log and change feed
  rev    INTEGER PRIMARY KEY AUTOINCREMENT,
  uav_id TEXT, type TEXT, data TEXT, at TEXT
);
```

Rules:

- sysid allocation: if the name hint is `drone_<n>`, and n is free and between
  1 and 239, use n. This keeps today's numbers. Otherwise use the lowest free
  number.
- Do not reuse the sysid of a retired drone for 24 hours. This avoids stale
  state in GCS tools.
- `event.rev` is the version of the registry content. It is also the identity
  bundle revision and the cursor for `/watch`.

## 5. API

Base path `/registry/v1`, port 1342. The platform already uses ports 1337–1341.

| Method | Path | Caller | Purpose |
|---|---|---|---|
| POST | `/join-tokens` | generator, operator (admin) | One-time join token (1 h) with a name hint and a group |
| POST | `/uavs/register` | drone (join token or signed assertion) | Create the drone's record, or return the existing one, with its allocation and an access token |
| POST | `/uavs/{id}/token` | drone (signed assertion) | New access token |
| PUT | `/uavs/{id}/lease` | drone, or the GCS for the drone | Renew presence and report `policy_rev` |
| GET | `/uavs?group=&state=` | edge services, GCS, coordinator | List drones |
| GET | `/uavs/{id}` | same | Read one drone |
| PATCH | `/uavs/{id}` | operator, context management | Change group, roles or state |
| DELETE | `/uavs/{id}` | operator | Retire the drone (the record stays) |
| GET | `/watch?since=<rev>` | GCS, coordinator | Changes after `rev` (long poll) |
| GET | `/.well-known/jwks.json` | anyone | Public keys to check tokens |
| GET | `/bundles/identity.tar.gz` | OPA instances | Signed OPA data bundle (section 8.2) |

Register request and response:

```json
POST /registry/v1/uavs/register
{
  "join_token": "Q3Jd...",
  "name_hint": "drone_101",
  "model": "gz_x500",
  "public_key": {"kty": "EC", "crv": "P-256", "x": "...", "y": "..."}
}

200 OK
{
  "uav_id": "drone_101",
  "spiffe_id": "spiffe://sagely/uav/drone_101",
  "sysid": 101,
  "group_id": "0",
  "endpoints": {
    "edge_url": "http://192.168.49.2:80",
    "gcs_host": "gcs_router",
    "gcs_port": 5760,
    "etcd": ["http://etcd:2379"]
  },
  "access_token": "eyJ...",
  "expires_in": 900,
  "jwks": {"keys": ["..."]}
}
```

## 6. Flows

### 6.1 Provision (generator)

1. For each planned drone, the generator calls `POST /join-tokens` with the
   name hint `drone_<i>` and the group from `input_config.yml`.
2. It writes `REGISTRY_URL`, `SAGELY_JOIN_TOKEN` and `UAV_NAME_HINT` into that
   drone's compose environment.
3. Static mode, for runs without a registry (for example offline
   experiments): the generator writes the same env file the registry would
   return, with `sysid = i`. The drone code works the same way in both modes.

### 6.2 Register, then boot

A new first tmuxinator pane, `sagely-identity`, starts before PX4:

1. It creates an ES256 key pair if there is none in the identity volume
   (`/var/lib/sagely/identity`).
2. It calls `POST /uavs/register`.
3. The registry checks the join token: it must exist, be unused and not be
   expired. Then the registry allocates the sysid, stores the record with state
   `provisioned`, and returns the allocation, the endpoints and a token.
4. The pane writes `/run/sagely/env` (`SYSID`, `UAV_ID`, `GROUP_ID`,
   `EDGE_URL`, `GCS_HOST`, `GCS_PORT`, `ETCD_ENDPOINTS`) and a token file. The
   other panes source the env file, and PX4 starts with `-i $((SYSID-1))`
   (Plan A).
5. The pane keeps running. It renews the lease and refreshes the token.
6. The first lease renewal sets the state to `active`. The registry writes an
   event, and two things follow:
   - The identity bundle gets a new revision, so the edge OPAs see the new
     drone after their next poll.
   - Context management gets a `uav_joined` notice.

```
generator        registry               sagely-identity        PX4/router/ROS      edge OPA
   | POST /join-tokens |                        |                     |                 |
   |------------------>|-- token                |                     |                 |
   | write env         |                        |                     |                 |
   |                   |<-- POST /uavs/register |                     |                 |
   |                   |-- sysid, token ------->| write /run/sagely/env                 |
   |                   |                        |-- start ----------->|                 |
   |                   |<-- PUT lease (every 3 s)                     |                 |
   |                   |   state=active, rev+1  |                     |                 |
   |                   |<-------------------------------------------------- poll bundle |
```

### 6.3 Restart

- The drone keeps its key pair in the identity volume. After a restart it
  calls `register` with a signed assertion instead of a join token. The
  registry finds the record by its public key and returns the same sysid. No
  new join token is needed.
- If the volume is lost, an operator creates a new join token. Then the
  registry creates a new record, or the operator replaces the key of the old
  record.

### 6.4 Token refresh

- An access token lives 15 minutes. The pane refreshes it after 10 minutes.
- To refresh, the drone signs a short assertion JWT with its private key:
  `iss` = `sub` = uav_id, `aud` = the token URL, `exp` at most 60 s, and a
  unique `jti`. It sends this to `POST /uavs/{id}/token`. This follows the
  client-assertion pattern of RFC 7523.
- The registry checks three things:
  - the signature, with the stored public key;
  - that the `jti` was not used before;
  - that the state is not `retired`.

### 6.5 Presence and loss

- A lease lives 10 s and is renewed every 3 s.
- If there is no renewal in time:
  1. The registry sets the state to `lost` and writes an event.
  2. Context management gets the event (at `/abnormal`, once L1 is fixed).
  3. Context management passes it to the planner.
- A drone with only a radio link (no IP route to the edge): the GCS renews the
  lease for it whenever it sees the drone's MAVLink heartbeat (Plan A). The
  lease records which source renewed it.
- `service_discovery` keeps its leader logic for now. It reads membership and
  presence from the registry instead of its own dicts (I4).

### 6.6 Group change

- Context management calls `PATCH /uavs/{id}` with `{"group_id": "1"}`,
  instead of only queueing a command (`context_management.py:151`).
- The registry records the change and raises the revision, so OPA data and the
  GCS see it.
- The drone learns its new group from the next lease response. The existing
  command can still trigger `client.py:482`.
- The token does not contain the group, so no new token is needed.
- The ID itself never changes. A "new ID" means: retire, then register again.

### 6.7 Retire

`DELETE /uavs/{id}` sets the state to `retired`. Token refresh then fails, and
OPA denies requests from this drone after its next poll of the identity bundle,
because the policies check `state == "active"` in OPA data (section 8). This
revokes access without waiting for the token to expire.

## 7. Tokens

Access token claims:

```json
{
  "iss": "sagely-registry",
  "sub": "spiffe://sagely/uav/drone_101",
  "aud": ["sagely-edge"],
  "uav_id": "drone_101",
  "sysid": 101,
  "iat": 1793000000,
  "exp": 1793000900,
  "jti": "5b0c..."
}
```

- The token has no roles and no group. They live in OPA data, so a change
  takes effect without a new token, and tokens stay small.
- Algorithm ES256. It works in Envoy `jwt_authn` (also 1.23 on the drone),
  Istio `RequestAuthentication`, OPA `io.jwt.decode_verify` and PyJWT. Current
  OPA also supports EdDSA (`io.jwt.verify_eddsa`), but ES256 works across all
  versions in this stack.
- Keep the registry's signing key in a Kubernetes Secret. During key rotation
  the JWKS holds both keys, told apart by `kid`.

## 8. Policies: identity in OPA data

### 8.1 Edge (Istio)

Add a `RequestAuthentication`:

```yaml
apiVersion: security.istio.io/v1
kind: RequestAuthentication
metadata:
  name: uav-jwt
spec:
  jwtRules:
    - issuer: sagely-registry
      jwksUri: http://uav-registry.platform-context.svc.cluster.local:1342/registry/v1/.well-known/jwks.json
      forwardOriginalToken: true   # keep the header, so that OPA can read the claims
```

Envoy then rejects invalid or expired tokens. A request with no token still
reaches OPA, and OPA denies it unless the path is public (the health check, or
`POST /registry/v1/uavs/register`).

The Rego below uses the same package and style as `policy_cluster.rego`, and
reuses its `trim_query`:

```rego
package istio.authz

import input.attributes.request.http as http_request

default allow := false

# The registry checks the join token itself.
allow if {
	http_request.method == "POST"
	http_request.path == "/registry/v1/uavs/register"
}

allow if {
	uav := data.uavs[claims.uav_id]
	uav.state == "active"
	some role in uav.roles
	some perm in data.role_perms[role]
	perm.method == http_request.method
	regex.match(perm.path, trim_query(http_request.path))
}

# Istio has already checked the token. Check it again with the key from the
# identity bundle, so OPA does not depend on the mesh config.
claims := payload if {
	[_, token] := split(http_request.headers.authorization, " ")
	[valid, _, payload] := io.jwt.decode_verify(token, {
		"cert": data.registry.jwks,
		"iss": "sagely-registry",
		"aud": "sagely-edge",
	})
	valid
}
```

- `role_perms` is policy, so it stays with the policy. Only "which drone has
  which role" moves to data.
- Give drones a `drone` role with only the drone endpoints, instead of `admin`
  (`policy_cluster.rego:77-79`).
- To fix S2, add an OPA sidecar and the AuthorizationPolicy to
  `platform-context` as well. If the platform services stay unprotected on
  purpose, write down why.

### 8.2 How OPA gets `data.uavs`

The registry serves a signed OPA bundle with the roots `uavs` and `registry`:

```json
{
  "uavs": {
    "drone_101": {"sysid": 101, "group": "0", "roles": ["drone"], "state": "active"}
  },
  "registry": {"jwks": "{\"keys\": [...]}"}
}
```

The edge OPA sidecars poll it. Add this to the OPA config in
`istio-opa/opa_config.yml`:

```yaml
services:
  registry:
    url: http://uav-registry.platform-context.svc.cluster.local:1342/registry/v1
bundles:
  identity:
    service: registry
    resource: /bundles/identity.tar.gz
    polling: {min_delay_seconds: 5, max_delay_seconds: 10}
    signing: {keyid: registry}
keys:
  registry:
    algorithm: ES256
    key: <registry public key, PEM>
```

- OPA allows several bundles, as long as their roots do not overlap. Check
  that the policy loaded from the `opa-policy` ConfigMap works next to a bundle
  in your OPA version. If it does not, ship the policy as a bundle too. You
  need that for signing anyway (8.4).
- Pushing with `PUT /v1/data/uavs` to each OPA is simpler, but it does not fit
  Kubernetes sidecars, which come and go. Use it only for a single OPA, for
  example on the GCS host.
- With polling, the edge can take up to `max_delay_seconds` to learn about a
  new drone. OPA also supports long polling, if the registry implements it,
  and delta bundles for small data changes.

### 8.3 Drone side

- The drone policy (`policy_drone_allow.rego:8`) checks a token instead of the
  fixed `"Basic drone_0:0"`.
- Envoy on the drone can check tokens with `jwt_authn`, using a local JWKS file
  from the register response. This also works offline.
- The drone only needs `data.uavs` if it has to authorize other drones or the
  GCS. This is still an open question.

### 8.4 Signed policy bundles

- The policy coordinator runs `opa check` and `opa test`, then builds and
  signs a bundle (`opa build --signing-key ...`). Each OPA verifies it, with
  `--verification-key` or with `signing` in its bundle config.
- At the edge, this replaces raw ConfigMap writes (S3).
- On the drone, the agent (Plan A) stores the bundle and OPA checks the
  signature. A faked MAVLink upload therefore cannot install a policy (S1).
- The coordinator keeps the policy signing key, not the registry. The registry
  only publishes public keys.

### 8.5 Research angle

`generate_policy.py:48-49` makes policies bigger by adding users and
permissions to the Rego. With identity in data, the policy stays small and
stable, and a joining drone is a small data change. A possible experiment:
measure the time from "a drone joins" to "the edge allows it" in three ways:

- (a) push the full policy;
- (b) send a data bundle;
- (c) send a delta bundle.

Repeat it for N = 10 to 1,000 drones.

## 9. Changes per file

| File | Change |
|---|---|
| new `src/sagely/uav_registry/` | FastAPI service with SQLite and a Dockerfile (same layout as `service_discovery/`) |
| new `src/sagely/k8s_deployment/policy_deployment/uav_registry.yml` | Deployment, Service (1342), PVC, Secret for the signing key |
| `src/sagely/k8s_deployment/istio/application_gateway.yml` | Route `/registry/` to `uav-registry` |
| `src/sagely/k8s_deployment/istio-opa/opa_config.yml` | Identity bundle config (8.2) |
| new `RequestAuthentication` manifest | 8.1 |
| `generation_drones/generate_configs.py`, `input_config.yml` | Join tokens or static mode; stop taking the instance from the loop index |
| `templates/docker-compose-per-drone.j2` | Registry env and identity volume |
| `templates/tmuxinator.j2` | First pane `sagely-identity`; the other panes source `/run/sagely/env` |
| `config/client_config.yaml` | Keep only app settings (`ds_path`, `rate`, `image_paths`); identity comes from registration |
| `client_drone/client.py:198-200` | `Authorization: Bearer <token>` from the token file |
| `client_drone/receive_ftp.py` (the agent) | `SYSID` from env; write the active revision to a file for the lease |
| `service_discovery/service_discovery.py` | Read membership and presence from the registry |
| `context_management/context_management.py:151` | Change groups through `PATCH /uavs/{id}` |
| `policy/policy_cluster.rego:73-79` | Remove `user_roles`; use `data.uavs` |
| `policy/policy_drone_allow.rego:8` | Check a token |
| `send_FTP_px4.py` or `policy_push.py` | Get targets from `GET /uavs?group=` |
| `scripts/entrypoint_etcd.sh`, `tmuxinator.j2:18` | Use one shared etcd from `ETCD_ENDPOINTS` (N1) |

## 10. Deployment

- Run the registry in the Kubernetes namespace `platform-context`, next to
  service discovery and context management.
- Store data in SQLite in WAL mode on a PVC, with one replica. Move to Postgres
  if you need more than one replica.
- Drones reach the registry through the gateway at `/registry/`. This only
  works once N2 is fixed, that is, once the drones are on a network that can
  reach the edge. For runs without the edge, run the same image with Docker
  Compose on the host, or use static mode.
- The GCS reads `/uavs` and `/watch` and keeps a local copy, so it can keep
  working if the link to the edge drops. While offline, it cannot register new
  drones (see the open questions).

## 11. Security model

| Threat | Today | With the registry |
|---|---|---|
| A client claims to be `drone_101` | Works, because the name alone gives access (I2) | Needs a valid token signed by the registry |
| A token is stolen | (no tokens) | 15-minute lifetime, `aud` check, `state` check in OPA data |
| A join token leaks from a compose file | (no join tokens) | Single use, 1-hour lifetime, tied to a name hint. Fine for SITL; use a secret store for real drones |
| A policy is changed on the way | Anyone with UDP access can do it (S1) | Signed bundles, checked by OPA |
| Platform endpoints are called directly | No OPA check (S2) | OPA sidecar and AuthorizationPolicy in `platform-context` |
| Misuse of the registry admin API | (no API) | Admin token, or the operator's mTLS identity |
| The registry key is stolen | (no key) | Kept in a Secret; short tokens; rotation with `kid` |

## 12. Implementation phases

**Phase 1: records and allocation** (I1, I3 in part, G6)
- Registry with `/join-tokens`, `/uavs/register`, and GET, PATCH and DELETE on
  `/uavs`.
- Static mode in the generator.
- The `sagely-identity` register step and the env file.

Done when:
- 4 drones start with no identity in `client_config.yaml`;
- each drone gets a unique sysid and a group;
- a restarted drone keeps its sysid;
- a 5th drone started later appears in `GET /uavs`, and in QGC with Plan A.

**Phase 2: presence** (I4)
- Leases, events to context management, and service discovery reading from the
  registry.

Done when stopping a drone sets it to `lost` within 10 s and sends context
management an event, and starting it again sets it to `active`.

**Phase 3: tokens** (I2, S2)
- JWKS, access tokens and refresh; Bearer tokens in `client.py`.
- `RequestAuthentication`, and OPA for `platform-context`.

Done when:
- a request without a token gets 403;
- an expired token gets 401;
- a retired drone gets 403 after one bundle poll;
- the `Basic` header is gone from the code.

**Phase 4: identity in OPA data** (I1)
- The identity bundle, a rewritten `policy_cluster.rego`, and token checks in
  the drone policy.

Done when a new drone can call `/preprocessing` without any Rego change.

**Phase 5: signed policy bundles** (S1, S3)
- The coordinator signs bundles. The edge and drone OPAs verify them, and the
  agent (Plan A) carries bundles.

Done when a changed or unsigned bundle is rejected both on the drone and at
the edge, and the GCS sees the rejection.

**Later:** SPIRE issues SVIDs with the same SPIFFE IDs.

## 13. Risks and open questions

Risks:

- New drones cannot join while the registry is down. Running drones keep
  working, because they have tokens and a cached JWKS.
- Bundle polling adds up to `max_delay_seconds` before the edge knows about a
  new drone.
- Clock differences break token checks. In SITL all containers share the host
  clock, but real drones need time sync.

Open questions:

- When can a retired drone's sysid be reused? (Proposal: after 24 hours.)
- Can drones join through the GCS when the edge cannot be reached? For example,
  a registry copy at the GCS could allocate from a reserved sysid range.
- Leader election: one shared etcd (proposal for now), or leases in the
  registry?
- Do drones need to authorize each other? If so, the drone OPA also needs
  `data.uavs`.
- Keep `drone_<n>` as the ID? (Proposal: yes, to avoid changes in code, logs
  and papers.)
