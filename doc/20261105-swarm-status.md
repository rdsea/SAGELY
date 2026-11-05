# Swarm stack: current status

Date: 2026-11-05 · Branch: `secassured/app` · Commit: `f42984f`

This note describes how the swarm stack works today and what breaks when many
drones run on one machine. It is the baseline for two plans:

- [Plan A: GCS control for many drones](20261105-plan-gcs-control.md)
- [Plan B: UAV identity and registry service](20261105-plan-identity-registry.md)

**How this was checked.** I read the code and the generated configs, and the
drone logs in `swarm_simulation/generation_drones/outputs/dockercompose_config/logs/`
(from 2026-11-05). I also checked the upstream source of PX4 (`main`, which is
what the Dockerfile builds), OPA and mavlink-router. Nothing was tested on
running containers. Each issue has an ID (G1, I2, ...) so the plans can refer
to it.

## 1. Summary

- The architecture is sound. Each drone has its own OPA + Envoy pair, the edge
  runs Istio + OPA, and there is a context → plan → enforce loop.
- The MAVLink policy push only works for one drone. It depends on a PX4 side
  effect and on fixed addresses that are baked into the image (G1–G4).
- A drone's identity is not defined in one place. It comes from an IP range and
  a loop counter, and is then copied by hand into six places (I1).
- There is no real authentication. A drone sends its name, plus its group ID as
  a "password", and no rule checks the password (I2).
- OPA does not check the platform endpoints at the edge (leader, heartbeat,
  commands) (S2). Anyone who can reach a drone's MAVLink ports can replace its
  policy (S1).
- Each drone runs its own one-member etcd, so every drone is a leader (N1).
- The edge control loop is not connected yet (L1–L3).

## 2. Architecture today

```
 Host (Docker)                                        Edge (minikube / kind)
+---------------------------------------------+      +-----------------------------------+
| Gazebo server (partition "relay")           |      | Istio ingress gateway             |
|                                             |      |  /preprocessing -> app  (default) |
| per drone i (one compose project):          | HTTP |  /notify-leader, /heartbeat, ...  |
|  drone_i container (tmuxinator)             |----->|     -> service discovery          |
|   PX4 SITL  px4 -i (i-start)                |      |  /notify-context, /get-command,   |
|   MicroXRCEAgent                            |      |     -> context management         |
|   ROS 2: client.py, receive_ftp.py          |      |     (namespace platform-context)  |
|   etcd (one member)                         |      |                                   |
|  envoy_i --ext_authz--> opa_i               |      | OPA-Istio sidecars (default ns),  |
|     \--> backend_i (http-echo)              |      |  policy from ConfigMap opa-policy |
|                                             |      |                                   |
| GCS scripts on the host:                    |      | planner / coordinator / change    |
|  send_FTP_px4.py, gcs.py, keyboard, (QGC)   |      | management: code only, no k8s     |
+---------------------------------------------+      +-----------------------------------+
```

| Path | Flow | Code |
|---|---|---|
| Images | `client.py` → edge `/preprocessing` | `swarm_simulation/src/client_drone/client_drone/client.py` |
| Leader and heartbeat | `client.py` (local etcd) → `/notify-leader`, `/heartbeat` → service discovery | `client.py`, `swarm_simulation/scripts/entrypoint_etcd.sh` |
| Commands | `client.py` polls `/get-command/...` from context management | `client.py:329`, `src/sagely/context_management/context_management.py` |
| Drone policy | `send_FTP_px4.py` → MAVLink → PX4 → `receive_ftp.py` → drone OPA | section 3 |
| Edge policy | `apply_policy_cluster.py` or coordinator → ConfigMap `opa-policy` → OPA sidecars (`--watch`) | `src/sagely/policy_controlplane/policy_coordinator/policy_coordinator.py` |
| Telemetry | PX4 → host UDP → `gcs.py` → edge | `swarm_simulation/src/ground_control_station/gcs.py` |

## 3. How the drone policy push works today

The push works, but not in the way the code suggests.

```
send_FTP_px4.py  --udpout-->  host 14560+100*offset  -->  drone :14560
                                                          PX4 link 3: -u 14560 -o 14561 -t 127.0.0.1
PX4 reads the custom header as a standard MAVLink FTP header:
   bytes 0-1 seq_number  <- the custom "opcode" 10 / 4 / 5
   byte  3   opcode      <- 0 = "none", so PX4 just answers ACK
PX4 reply: seq_number + 1, data echoed  -->  127.0.0.1:14561  -->  receive_ftp.py
receive_ftp.py reads byte 0 as the opcode: 11 / 5 / 6
receive_ftp.py --PUT--> drone OPA
receive_ftp.py --NAMED_VALUE_FLOAT "OPA<code>"--> 127.0.0.1:14570 --> PX4
PX4 streams it again, with its own sysid, on all links
   --> 192.168.49.1:14551 and 192.168.132.1:14553 --> sender (it takes the first one)
```

Code: header `send_FTP_px4.py:113`, target `:116`, opcodes `:131,135,137`.
Receiver checks `receive_ftp.py:44,50,56`. Links `swarm_simulation/config/px4-rc.mavlink:26,30,35`.

This explains the opcode offset (10/4/5 in the sender, 11/5/6 in the receiver).
It also means the transfer stops working as soon as the target, the routing or
PX4's FTP handling changes.

## 4. What works

- The generator writes compose, Envoy and tmuxinator configs for each drone and
  finds a free network (`swarm_simulation/scripts/network_setup.sh`).
- PX4 SITL runs with a shared Gazebo server (partition `relay`).
- OPA + Envoy start for each drone. The policy ID is correct: OPA stores a file
  loaded at startup under its path without the leading `/`, so
  `/policy/policy.rego` becomes `policy/policy.rego`. That is the ID in the
  template's `OPA_URL` (`docker-compose-per-drone.j2:62`), so a PUT replaces
  the startup policy. The default in `receive_ftp.py:22` (`policy.rego`) would
  not match. A different ID adds a second module, which causes the "multiple
  default rules" error in `swarm_simulation/docs/README.md:487-500`.
- The MAVLink policy push works for one drone (sysid 1). This matches the ICWS
  setup, which had one machine per drone.
- At the edge: Istio with OPA-Istio injection, policy reload from the
  ConfigMap, and Jaeger tracing.

## 5. Issues

### 5.1 GCS and MAVLink (G)

**G1. The policy push only reaches sysid 1.**
`send_FTP_px4.py:116` hard-codes `target_system=1`. PX4 sets
`MAV_SYS_ID = instance + 1`, and the generator starts drone *k* of a batch with
`px4 -i {i - start}` (`generate_configs.py:105,113`). PX4's FTP server ignores
requests for other system IDs (it accepts its own ID or 0). In a batch, only
the first drone answers. For the other drones, the sender waits until it times
out.

**G2. The transfer depends on a PX4 side effect (section 3).**
- There is no retransmission and no checksum, so a lost chunk goes unnoticed.
- `.strip()` on each chunk (`receive_ftp.py:41`) removes spaces and newlines
  at the 239-byte chunk edges. This can change or break the Rego.
- The receiver handles at most one FTP message per 100 ms tick
  (`receive_ftp.py:9,30,37`), about 2.4 KB/s of policy. A faster sender
  relies on the socket buffer, and nothing is resent if it overflows.

**G3. Every drone uses the same MAVLink addresses.**
`config/px4-rc.mavlink` is copied into the image before PX4 is built
(`Dockerfile:48,54`). So every drone has the same links, with fixed partners
`192.168.49.1:14551` and `192.168.132.1:14553` (`px4-rc.mavlink:26,30`). These
addresses are only correct if `network_setup.sh` happens to pick those
networks. All drones send their acks to the same host ports. The ack text
(`OPA<code>`) contains no drone ID and no policy version. The sender takes the
first ack and does not check `msg.get_srcSystem()` (`send_FTP_px4.py:151-175`).
Note: the comments at `px4-rc.mavlink:27,31-32,36-37` describe `-u` and `-o`
the wrong way round. The commands themselves are correct: `-u` is the local
port, `-o` the remote port, and `-t` fixes the partner address.

**G4. Drones hear each other.**
The GCS link is started with `-p -n eth0` (`px4-rc.mavlink:39`). With `-p`,
PX4 sends every message on that link to the subnet broadcast address on port
14550 until a GCS connects (`mavlink_main.cpp`, `send_finish()`). Every drone
binds UDP 14550 (`px4-rc.mavlink:30`), so each drone receives the streams of
all the other drones, and `-f` lets PX4 forward them to its other links. PX4
SITL also sends this stream to 127.0.0.1:14550 by default, and inside the
container that port is PX4's own link from line 30. Upstream PX4 adds
`-n ... -p` only when `PX4_NET_INTERFACE` is set. Traffic grows with N², and
every drone sees foreign system IDs.

**G5. The first drone takes host UDP ports 14550 and 14560.**
The template publishes `14560+100*offset` and `14550+100*offset` on all host
interfaces (`docker-compose-per-drone.j2:69-71`, `offset = i - start`). For
drone_101 the offset is 0, but QGC, `gcs.py:158-159` and
`keyboard-mavsdk-test.py:62` also want host port 14550.

**G6. Instance numbers restart at 0 for every batch.**
From the instance number, PX4 derives three names:
- the MAVLink sysid (instance + 1);
- the uXRCE-DDS namespace (`uav_<instance>`, and no namespace at all for
  instance 0);
- the Gazebo model name (`<model>_<instance>`, spawned with
  `allow_renaming: false`).

A second batch therefore collides on all three. Also, all drones use ROS 2
domain 0 (`ROS_DOMAIN_ID` is set nowhere) and the same node names
(`client.py:94`, `receive_ftp.py:14`). If DDS discovery reaches across
containers, the node names and the `mavlink_ftp_data` topic collide.

**G7. `gcs.py` forwards everything.**
It opens a new HTTP session for every MAVLink message (`gcs.py:126`), and
unknown message types go to `/notify-leader` (`gcs.py:122-124`). So every
telemetry message becomes an HTTP POST to the edge. The second loop
(`gcs.py:150-154`) never runs.

### 5.2 Identity and authentication (I)

**I1. Identity is copied by hand into six places.**

| Where | What |
|---|---|
| `swarm_simulation/generation_drones/input_config.yml` | `start_ip` / `end_ip`, which give the drone names and IPs |
| `swarm_simulation/config/client_config.yaml` | `device_id` and `group_id` for each drone |
| `policy_change_management/policy/policy_cluster.rego:73-79` | `user_roles` (only drone_101–103) |
| `policy_change_management/policy/policy_drone_allow.rego:8` | `"Basic drone_0:0"` |
| `send_FTP_px4.py:20`, `config/send_uav_config.yaml` | FTP target list |
| `generate_configs.py:105` | PX4 instance, and so the sysid |

`README.md:136` already warns that these must match. They already drift:
drone_104 has no entry in `client_config.yaml`, so its client never connects
to etcd and logs `'NoneType' object has no attribute 'lock'` 46 times.

**I2. There is no authentication.**
`client.py:200` sends `Authorization: Basic <device_id>:<group_id>`. The value
is not base64, and the "password" is the group ID.
- `policy_cluster.rego:55-59` parses the password, but no rule uses it. The
  drone name alone decides access.
- The bootstrap edge policy decodes base64 (`opa_config.yml:82`), so drone
  requests fail until the cluster policy is applied.
- `service_discovery.py:108` uses `Basic admin:admin`.

Anyone who knows a drone's name can act as that drone.

**I3. Group changes are not recorded centrally.**
Context management can tell a drone to change its group
(`/send-command/change-group-or-id`, `context_management.py:151`), and the
drone then changes it locally (`client.py:482`). No policy, config or
registry is updated.

**I4. Presence is kept only in memory.**
`service_discovery.py` keeps `current_leaders` and `last_heartbeat` in Python
dicts, and only group leaders send heartbeats. A restart loses this state, and
drones that are not leaders are invisible.

### 5.3 Policy integrity and enforcement (S)

**S1. Anyone who can reach a drone's MAVLink ports can replace its policy.**
Host UDP `14560+100*offset` is published on all interfaces, and the receiver
listens on `0.0.0.0:14561` inside the drone container. PX4 accepts messages
from any source on a `-t` link, and `receive_ftp.py` uploads whatever it puts
together. There is no signature check and no sender check.

**S2. OPA does not check the platform endpoints.**
`istio-opa/opa_authz.yml` has no namespace and no selector, so the `CUSTOM`
check only applies in the namespace it is applied to (`default`, where the
application runs). Service discovery and context management run in
`platform-context` (`istio/application_gateway.yml:34,60`). That namespace gets
Envoy sidecars but no OPA sidecar and no AuthorizationPolicy
(`infrastructure/Tiltfile:90-98`). As a result:
- The rules for `/notify-leader`, `/heartbeat` and `/send-command/...` in
  `policy_cluster.rego:88-97` never run.
- Anyone who can reach the gateway can, for example, change a drone's group.

**S3. Edge policy updates are not checked before rollout.**
The coordinator replaces the `opa-policy` ConfigMap, which every OPA sidecar
watches. No `opa check` or test runs first. The planner also generates Rego
without a `package` line (`policy_planner.py:11`). A bad policy reaches every
sidecar at the same time.

**S4. The drone's PEP protects only a test service.**
The drone's Envoy protects `backend_<i>` (`http-echo`,
`docker-compose-per-drone.j2:73-79`). Images sent to the edge, MAVLink traffic
and ROS 2 traffic do not pass through it.

### 5.4 Networking and coordination (N)

**N1. Every drone is its own leader.**
`tmuxinator.j2:18` starts a one-member etcd inside each drone. All four logs
show "Campaigning for leadership". drone_101 and drone_103 are both in group 0
(`client_config.yaml:3,21`), so both report as leader of group 0.

**N2. The drones cannot reach the edge.**
- drone_101, 102 and 103 log `No route to host` for 192.168.49.2 (968, 391 and
  211 times) and timeouts (134, 75 and 39 times).
- `client_config.yaml:4` hard-codes the minikube IP, but the generated configs
  use `swarm_net` (192.168.132.0/24), because the generator did not find the
  minikube network.
- By default, Docker does not route between separate bridge networks.
  "No route to host" also suggests that minikube was not running.

**N3. The address plan has limits.**
- The sidecar subnet `192.168.<i>.0/24` (`docker-compose-per-drone.j2:11`) is
  the swarm subnet when i = 132.
- Envoy's swarm address `.<i+100>` (`generate_configs.py:92`) is invalid for
  i ≥ 155.
- If drones join the minikube network, the MetalLB range (from the minikube IP
  to `.255`, `infrastructure/Tiltfile:37`) overlaps the drone addresses.

### 5.5 Edge control loop (L)

**L1. Some URLs are wrong.**
- `service_discovery.py:22` calls `/abnormal-detect`, but context management
  serves `/abnormal`.
- `context_management.py:19` calls `policy-planner:8000/policy-planner`, but
  the planner serves `/develop_plan` (`policy_planner.py:84`) on port 1339
  (`:108`).

**L2. Parts are missing.** There are no Kubernetes manifests for the planner,
the coordinator or change management. `policy_enforcer.py` is empty, and
change management only prints its steps.

**L3. `/send-command/change-task-parameter` always fails.** It uses
`ON CONFLICT(node_id, command_type)` (`context_management.py:186`), but the
`commands` table has no `node_id` column and no unique key (`:55-59`).

**L4. Context is lost on restart.** Context management writes a DuckDB file
with no volume (`context_management.py:21`).

**L5. An error looks like success.** `service_discovery.py:87` raises
`HTTPException(status_code=200)` for an unknown leader.

### 5.6 Reproducibility (R)

**R1. Versions are not pinned:**
- PX4 `main` (`Dockerfile:52`), although the docs say 1.15;
- `opa:latest-envoy` (`docker-compose-per-drone.j2:29`);
- `opa:latest-istio` (`opa_controller.yml:157`);
- Envoy `v1.23-latest` (`docker-compose-per-drone.j2:18`), which is no longer
  supported.

A re-run of the ICWS experiments may behave differently.

**R2. Some generator settings are ignored or repeated:**
- `px4_gz_model_pose` is under `drone:` in `input_config.yml`, but the code
  reads it from the gazebo section, so it is ignored.
- The configured `gz_ip` is replaced (`generate_configs.py:94`).
- The PX4 pane runs `sleep 3` twice.

## 6. Suggested order

| Step | What | Fixes | Where |
|---|---|---|---|
| 1 | Quick unblock: target 0, chunk parsing by `size`, drain loop, check source sysid, remove host port 14550 | G1, G2 (part), G3 (part), G5 | Plan A, phase 0 |
| 2 | Registry with sysid allocation, register then boot | I1, I3, G6, N2 (part) | Plan B, phase 1 |
| 3 | MAVLink routers, agent as a MAVLink component, stock PX4 rc file | G2–G4, G7, S1 (ports) | Plan A, phases 1–3 |
| 4 | Presence and tokens, OPA on platform endpoints | I2, I4, S2 | Plan B, phases 2–3 |
| 5 | Identity in OPA data, signed policy bundles | I1, S1, S3 | Plan B, phases 4–5 |
| any | Small fixes | N1, N3, L1–L5, R1, R2, S4 | none |
