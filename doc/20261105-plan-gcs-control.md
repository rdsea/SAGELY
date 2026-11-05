# Plan A: GCS control for many drones

Date: 2026-11-05 · Status: proposal
Baseline: [current status](20261105-swarm-status.md) · Related: [Plan B: identity and registry](20261105-plan-identity-registry.md)

## 1. Problem

The GCS scripts were built for one drone per machine (the ICWS setup). With
many drone containers on one host, they fail for these reasons:

- the policy push always targets system ID 1 (G1);
- the transfer depends on PX4 echoing FTP requests it does not understand (G2);
- every drone has the same MAVLink addresses, baked into the image (G3);
- drones broadcast their MAVLink streams to each other (G4);
- the first drone takes host port 14550 (G5);
- IDs restart at 0 for every batch (G6).

## 2. Goals and non-goals

Goals:

1. Run N drones on one host, and later on several hosts, without publishing
   MAVLink ports for each drone.
2. Every GCS tool (QGC, `gcs.py`, policy push, keyboard control) can reach any
   drone by its MAVLink system ID.
3. The policy push is reliable and can be checked. It has retries and a
   checksum, and each drone answers with the policy revision that is now
   active.
4. The GCS can run on the same host or on another machine, with no change to
   the drone image.
5. Only trusted senders can change a drone's policy (together with Plan B).

Non-goals:

- Simulating real radio links. Keep `swarm_simulation/scripts/add_latency.sh`
  for delay and loss.
- Changing PX4's own FTP server.
- A new GCS user interface. QGC stays the UI.

## 3. Decisions

**D1. Address every drone by a unique MAVLink system ID (sysid).**
- The registry in Plan B allocates the sysid. Until then, the sysid is the
  drone number (`drone_101` gets 101).
- Start PX4 with `px4 -i $((SYSID-1))`. PX4 sets `MAV_SYS_ID = instance + 1`.
- Vehicles use 1–239. Ground tools use 240–255: QGC and pymavlink default to
  255, MAVSDK to 245, and the policy push will use 250.
- PX4 `main` allows IDs above 255 through a new MAVLink 2 extension. But
  pymavlink, QGC and mavlink-router use 8-bit IDs, so stay at 255 or below.

**D2. Route MAVLink instead of publishing ports.**
- One `mavlink-routerd` runs inside each drone container (the onboard router),
  and one central router runs on the GCS side.
- Each onboard router opens a TCP connection to the central router.
- Why TCP: a mavlink-router UDP server endpoint sends to the last peer it heard
  from (mavlink-router README, "Behavior in server mode"). With many drones on
  one UDP port, replies would go to the wrong drone. TCP gives one connection
  per drone, reconnects by itself (`RetryTimeout`), and works through NAT.
- mavlink-router remembers which sysid/compid pairs it has seen on each
  endpoint. A message with a target goes only to the endpoint where that
  target was seen. A message without a target goes to all other endpoints.

**D3. The policy agent becomes a MAVLink component.**
- It uses the drone's sysid with compid 191 (`MAV_COMP_ID_ONBOARD_COMPUTER`),
  and sends a HEARTBEAT at 1 Hz.
- GCS tools send to `(sysid, 191)`. PX4 is no longer in the policy path, so
  the echo side effect (G2) goes away.

**D4. Upload with standard MAVLink FTP, then activate with a command.**
- Upload: the agent implements a small part of the MAVLink FTP server
  (section 5.4). Standard clients can then be used for tests, for example the
  `ftp` module of MAVProxy, or the MAVSDK FTP plugin with target compid 191.
- Activate: `COMMAND_LONG` with `MAV_CMD_USER_1` (31010), where param1 is the
  revision. The agent answers with `COMMAND_ACK`: first `IN_PROGRESS`, then
  `ACCEPTED` or `FAILED`, with `result_param2` set to the revision or an
  error code.
- Two phases, first upload to all drones and then activate all, shorten the
  time in which drones of one group run different policies. This fits
  SAGELY's goal of consistent policy across the swarm.

**D5. Keep PX4's MAVLink setup stock.**
- Remove the custom `px4-rc.mavlink` from the image (`Dockerfile:48,54`).
- PX4's GCS link then sends to 127.0.0.1:14550, where the onboard router
  listens, without broadcast. Upstream adds `-p` only when
  `PX4_NET_INTERFACE` is set.
- If you need a change, for example different stream rates, keep a small
  override that contains only that change.

**D6. The drone gets the GCS address from its environment.**
- The address comes from `GCS_HOST` and `GCS_PORT`, set by the generator now
  and by the registry later.
- Same host: `gcs_router` (the Docker DNS name on the shared network) and
  port 5760.
- Another machine: that machine's address through a VPN or an SSH tunnel.
  mavlink-router has no TLS.
- mavlink-router only accepts IP addresses, not host names (it calls
  `inet_addr` / `inet_pton`). Resolve the name with `getent hosts` first.

## 4. Architecture

```
 drone_101 container                          gcs_router container (same host)
+-----------------------------------+        +--------------------------------------+
| PX4  sysid 101  (stock rc file)   |        | mavlink-routerd                      |
|   GCS link --> 127.0.0.1:14550    |        |   TCP server :5760                   |
|                                   |  TCP   |     <-- onboard router of each drone |
| mavlink-routerd (onboard) --------+------->|     <-- policy push, gcs.py          |
|   UDP server 127.0.0.1:14550 (PX4)|        |         (host: 127.0.0.1:5760)       |
|   UDP client 127.0.0.1:14561      |        |   UDP client --> host:14550 (QGC)    |
|   TCP client gcs_router:5760      |        |   routes by target sysid/compid      |
|                                   |        +--------------------------------------+
| policy agent  sysid 101, comp 191 |
|   udpin 127.0.0.1:14561 --> OPA   |
+-----------------------------------+
 drone_102 ... the same with sysid 102 --------> same :5760.  No host ports per drone.
```

## 5. Components

### 5.1 PX4

- Start with `px4 -i $((SYSID-1))`. This replaces `-i {i - start}` in
  `generate_configs.py:105,113`.
- The names PX4 derives from the instance are now unique: DDS namespace
  `uav_$((SYSID-1))` and Gazebo model `<model>_$((SYSID-1))`. If you want the
  namespace to match the sysid, set `PX4_UXRCE_DDS_NS=uav_${SYSID}`. The
  current ROS 2 code does not subscribe to PX4 topics, so this does not break
  anything.
- PX4 offsets some ports by the instance number. This is not a problem, because
  each container has its own network namespace.

### 5.2 Onboard router

A tmuxinator pane, started before the agent:

```sh
while true; do
  GCS_IP=$(getent hosts "$GCS_HOST" | awk '{print $1; exit}')
  mavlink-routerd -t 0 -p "$GCS_IP:$GCS_PORT" -e 127.0.0.1:14561 127.0.0.1:14550
  sleep 2   # resolve again if the central router got a new IP
done
```

- `-t 0` turns off the TCP server inside the drone.
- `-p` adds a TCP client to the central router.
- `-e 127.0.0.1:14561` adds a UDP client to the agent.
- The last argument is a UDP server for PX4's GCS link.
- Build mavlink-router from source in the Dockerfile (meson + ninja,
  `git submodule update --init --recursive`), and pin the release tag `v4`.
- For filters (section 7), use a config file (`-c`) instead of flags.

### 5.3 Central router

The generator writes one extra compose file,
`outputs/dockercompose_config/docker-compose-gcs.yml`:

```yaml
services:
  gcs_router:
    image: <drone image>              # it already contains mavlink-routerd
    container_name: gcs_router
    extra_hosts: ["host.docker.internal:host-gateway"]
    volumes: ["../../../scripts/gcs_router.sh:/gcs_router.sh:ro"]
    entrypoint: ["/bin/sh", "/gcs_router.sh"]
    ports: ["127.0.0.1:5760:5760"]    # tools on this host only, not the LAN
    networks: [<swarm network>]
networks:
  <swarm network>:
    external: true
```

`swarm_simulation/scripts/gcs_router.sh` (new):

```sh
#!/bin/sh
# QGC runs on the host. mavlink-router needs an IP, not a name.
HOST_IP=$(getent hosts host.docker.internal | awk '{print $1; exit}')
exec mavlink-routerd -e "$HOST_IP:14550"
```

- mavlink-router's TCP server listens on 5760 by default (`TcpServerPort`).
- Ground tools on the host connect to `tcp:127.0.0.1:5760`.
- QGC listens on UDP 14550 as usual. It sees every vehicle over one link.

### 5.4 Policy agent (replaces `receive_ftp.py`)

Identity and link:

- sysid from `SYSID`, compid 191, connection `udpin:127.0.0.1:14561`.
- HEARTBEAT at 1 Hz with `MAV_TYPE_ONBOARD_CONTROLLER`, so that the routers
  learn the component.
- The agent accepts a message only if its target is `(SYSID, 191)`.

FTP server subset. The header is standard: `seq_number` u16, `session`,
`opcode`, `size`, `req_opcode`, `burst_complete`, `padding` (u8 each),
`offset` u32, then up to 239 bytes of data.

| Opcode | Name | Agent behaviour |
|---|---|---|
| 2 | ResetSessions | Close all sessions and delete partial files |
| 6 | CreateFile | Open `staging/<name>` for writing and return the session |
| 7 | WriteFile | Write `size` bytes at `offset` (the same write twice is harmless) |
| 14 | CalcFileCRC32 | Return the CRC32 of the staged file |
| 1 | TerminateSession | Close the file |
| 128 / 129 | ACK / NAK | Replies use `seq_number + 1` and `req_opcode` set to the request's opcode |

- If a request has the same `seq_number` as the previous one, send the
  previous reply again. A lost ACK then does not cause a second action.
- Read exactly `size` bytes of data. Never strip.

Activation and status:

1. `COMMAND_LONG` `MAV_CMD_USER_1`, param1 = revision → `COMMAND_ACK IN_PROGRESS`.
2. Check the staged file. In Plan B, also check its signature.
3. Apply it to OPA. Today that is a `PUT` to `OPA_URL`, with the ID unchanged
   (`policy/policy.rego`). Later it is a signed bundle (Plan B, phase 5).
4. `COMMAND_ACK ACCEPTED` with `result_param2 = revision`, or `FAILED` with an
   error code. Also send a `STATUSTEXT` for people.
5. Send `NAMED_VALUE_INT "pol_rev"` every second, so the GCS always knows the
   active revision of each drone.

### 5.5 Ground tools

| Tool | Change |
|---|---|
| `send_FTP_px4.py`, later `policy_push.py` | One connection `tcp:127.0.0.1:5760` with `source_system=250`. Targets are sysids (or a group, through Plan B). For each drone: upload with retries, check the CRC, activate, and wait for the `COMMAND_ACK` whose source is `(sysid, 191)`. Handle drones in parallel over the same connection, and keep the latency CSV used in the ICWS experiments. |
| `gcs.py` | `tcp:127.0.0.1:5760` with `source_system=251`. Use one `aiohttp.ClientSession`. Forward only a list of message types, and add the sysid to each payload. Remove the fallback to `/notify-leader` and the dead loop (`gcs.py:150-154`). |
| QGC | No change: it listens on UDP 14550 on the host. |
| Keyboard controller (MAVSDK) | MAVSDK's `System` takes the first autopilot it finds, so give each drone its own endpoint at the central router (section 7, `kb_101`). Then `drone.connect("udp://:14601")`. |

## 6. Message flows

Start-up:

1. PX4 sends its GCS stream to 127.0.0.1:14550, and the onboard router learns
   `(101, 1)`.
2. The agent sends heartbeats, and the onboard router learns `(101, 191)`.
3. The onboard router connects to `gcs_router:5760`. The central router learns
   `(101, 1)` and `(101, 191)` on that connection.

Policy push to group 0, here drones 101 and 103:

```
policy_push (250,190)             gcs_router              drone 101 agent    drone 103 agent
  CreateFile/WriteFile/... -----> route by target ------> (101,191)
  CreateFile/WriteFile/... -----> route by target ---------------------------> (103,191)
  CalcFileCRC32 x2         <----- ACK with CRC   <------- both
  MAV_CMD_USER_1 rev=42 x2 -----> ------------------------> both
  COMMAND_ACK (src 101 / 103) <-- ----------------------- ACCEPTED, result_param2=42
```

Telemetry: PX4 → onboard router → central router → QGC, `gcs.py`, and, without
filters, the other drones (section 7).

## 7. Scaling

- The central router sends every message without a target to all other
  endpoints, including the connections of the other drones. If one drone sends
  R bytes/s, the drones receive about N·(N−1)·R bytes/s in total. Measure R
  with `ReportStats = true` (or `-r`).
- For a few SITL drones, this does not matter. Add the following steps only
  when the measurement shows a problem:
  1. Lower PX4's stream rates on the GCS link (`mavlink stream -r`).
  2. Drop other drones' traffic where it enters a drone. Put this in the
     onboard router's config file:
     ```ini
     [TcpEndpoint uplink]
     Address = <gcs ip>
     Port = 5760
     AllowSrcSysIn = 250,251,255      ; only ground tools may enter
     ```
  3. Stop the fan-out at the central router. Give each drone its own UDP
     server port (for example 15000 + sysid) with
     `AllowSrcSysOut = <ground sysids>`. Each port then has exactly one peer.
     Because the config is static, create the ports for the whole sysid range
     in advance.
- A per-drone endpoint for MAVSDK tools at the central router:
  ```ini
  [UdpEndpoint kb_101]
  Mode = Normal
  Address = <host ip>
  Port = 14601
  AllowSrcSysOut = 101                ; this tool sees only drone 101
  ```

## 8. Security

- Today, anyone who can reach UDP 14560 or 14561 can install a policy (S1).
- After phase 1, drones publish no ports. The central router can be reached
  only from the Docker network and from `127.0.0.1` on the host.
- The agent accepts FTP and commands only from ground sysids (240–255). This
  is cheap but weak, because a sysid can be faked.
- Real protection comes from Plan B:
  - Signed policy bundles: the agent or OPA rejects any policy that is not
    signed.
  - Optionally, MAVLink 2 signing between ground tools and the agent
    (pymavlink supports it), with a key for each drone from the registry. This
    blocks fake activate commands and replays.

## 9. Implementation phases

### Phase 0: quick unblock (no new components, no image rebuild)

| Task | File |
|---|---|
| Set `target_system=0`. Each `udpout` reaches one container, and PX4 accepts 0. | `send_FTP_px4.py:116` |
| Read exactly `size` bytes: `bytes(payload[12:12 + payload[4]])`. Remove the per-chunk `.strip()`. | `receive_ftp.py:41` |
| Handle all waiting messages in each tick, not just one. | `receive_ftp.py:37` |
| Accept an ack only if `msg.get_srcSystem()` is the drone's sysid (`i - start + 1`). Use one listener socket for all drones and dispatch by sysid. Several sockets on one port with `SO_REUSEADDR` do not each get a copy. | `send_FTP_px4.py:141-175` |
| Generate the target list (name, `udpout:127.0.0.1:<14560+100*offset>`, sysid) instead of editing it by hand. | `generate_configs.py`, `config/send_uav_config.yaml` |
| Remove the 14550 mapping. Bind 14560 to `127.0.0.1` only. | `docker-compose-per-drone.j2:69-71` |

Done when the push succeeds for each of 4 drones, each ack comes from the
expected sysid, and the policy in each OPA matches the source file byte for
byte:

```sh
curl -s http://192.168.101.3:8181/v1/policies/policy/policy.rego | jq -r .result.raw | diff - <policy file>
```

### Phase 1: routing and a minimal agent (image rebuild)

The old echo path stops working once routing is in place, so the agent change
must ship in the same phase.

| Task | File |
|---|---|
| Build mavlink-router `v4`. Stop copying `px4-rc.mavlink`. | `swarm_simulation/Dockerfile` |
| `px4 -i {sysid - 1}` with `sysid = i`; fail if i > 239. Set `SYSID`, `GCS_HOST` and `GCS_PORT`. | `generate_configs.py:105,113` |
| Add the router pane (section 5.2). | `templates/tmuxinator.j2` |
| Remove `ports:`. Write `docker-compose-gcs.yml` and add `scripts/gcs_router.sh` (section 5.3). | `templates/docker-compose-per-drone.j2`, new template, new script |
| Agent: `source_system=SYSID, source_component=191`, heartbeat, accept only target `(SYSID, 191)`, opcodes 10/4/5 now arrive unchanged (no +1), reply on the same connection. | `receive_ftp.py` |
| Sender: `tcp:127.0.0.1:5760`, `source_system=250`, target `(sysid, 191)`, match acks by `(sysid, 191)`. | `send_FTP_px4.py` |
| `gcs.py` over `tcp:127.0.0.1:5760`. | `gcs.py:113-114,157-159` |

Done when:
- QGC shows all N vehicles;
- the script in section 10 lists `(sysid, 1)` and `(sysid, 191)` for every
  drone;
- `docker ps` shows no published ports for drones;
- one sender connection can push to every drone by sysid.

### Phase 2: reliable transfer

- Agent: the FTP subset, activation and status from section 5.4.
- `policy_push.py` with retries, CRC check, two-phase activation and per-drone
  results.

Done when:
- a 300 KB policy arrives intact with 10 % packet loss (`tc netem`) and the
  ack reports the right revision;
- sending the same revision again changes nothing;
- a wrong CRC gives a NAK and no activation.

### Phase 3: tools and scale

- Clean up `gcs.py` (section 5.5) and add the keyboard endpoints.
- Measure the fan-out, then add the filters from section 7 if needed.
- Remote GCS: tunnel, with `GCS_HOST` and `GCS_PORT` from the environment
  (later from the registry).

### Phase 4: security (with Plan B)

- The agent requires a signed bundle (Plan B, phase 5).
- Optionally, MAVLink 2 signing with a key for each drone.

## 10. Checks

List the components the central router can see:

```python
import time
from pymavlink import mavutil

m = mavutil.mavlink_connection("tcp:127.0.0.1:5760", source_system=250)
seen, end = set(), time.time() + 5
while time.time() < end:
    hb = m.recv_match(type="HEARTBEAT", blocking=True, timeout=1)
    if hb:
        seen.add((hb.get_srcSystem(), hb.get_srcComponent()))
print(sorted(seen))  # expect (101, 1), (101, 191), (102, 1), (102, 191), ...
```

- Ports: `docker ps --format '{{.Names}} {{.Ports}}'`.
- Router traffic: `ReportStats = true` in the config, or `-r`.
- Active policy: `GET /v1/policies/policy/policy.rego` on each drone OPA, or
  watch the `pol_rev` values.

## 11. Risks and open questions

Risks:

- mavlink-router must be built from source, which makes the image build
  longer. Pin `v4`.
- mavlink-router needs IP addresses, so the restart loop in section 5.2 must
  resolve the name again.
- Over a lossy WAN, one TCP connection can stall all its traffic while a lost
  packet is resent. If that hurts, use per-drone UDP ports (section 7, step 3).
- MAVLink FTP moves one 239-byte chunk per round trip. At 50 ms RTT, a 300 KB
  policy (about 1,260 chunks) takes about 63 s. Options: let the agent accept
  a small window of writes in flight, or pull the bundle over HTTP when the
  drone has an IP route to the edge (Plan B).
- The latency numbers will differ from the ICWS results, because the path
  changes. Measure a new baseline.
- PX4 `main` is not pinned (R1). Pin it before you rely on PX4 behaviour.

Open questions:

- Do drones need each other's MAVLink traffic, for example for swarm
  coordination? If not, filter at the central router from the start.
- Should drones that have an IP route get policies directly from the edge?
  Then the OPA bundle pull (Plan B) is the main path, and MAVLink is the
  fallback for drones with only a radio link.
- Where does the GCS run in the target scenario: on the same host, on the same
  LAN, or in the cloud?
