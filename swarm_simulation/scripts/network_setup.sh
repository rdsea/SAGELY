#!/usr/bin/env bash
# use_or_create_network.sh
# Reuse Minikube network if present, otherwise create a new docker bridge network.
set -euo pipefail

# ----- Configurable env inputs (can be set outside before calling) -----
# NETWORK_NAME (optional): preferred name for new network (default: swarm_net)
# PREFER_MINIKUBE (optional): 1 to try reusing minikube network first (default: 1)
# BASE_IP (optional): prefix for created networks (default: "192.168")
# SWARM_SUBNET (optional): starting third-octet candidate (default: 132)
# TRIES (optional): how many subnets to probe (default: 200)

TARGET_BASE_NAME="${NETWORK_NAME:-swarm_net}"
PREFER_MINIKUBE="${PREFER_MINIKUBE:-1}"
BASE_PREFIX="${BASE_IP:-192.168}"
BASE_PREFIX="$(echo "$BASE_PREFIX" | sed 's/\.$//')" # normalize (no trailing dot)
SWARM_SUBNET_OCTET="${SWARM_SUBNET:-132}"
TRIES="${TRIES:-200}"

# helpers
die() {
  echo "ERROR: $*" >&2
  exit 1
}
docker_exists() { command -v docker >/dev/null 2>&1; }
minikube_exists() { command -v minikube >/dev/null 2>&1; }
get_network_subnet() {
  docker network inspect "$1" -f '{{range .IPAM.Config}}{{.Subnet}}{{end}}' 2>/dev/null || echo ""
}

# ensure docker available
if ! docker_exists; then
  die "docker CLI not found. This script needs docker to inspect/create networks."
fi

SELECTED_NETWORK=""
SELECTED_SUBNET=""
MK_IP=""

# 1) Try to discover an existing minikube-related network (if preferred)
if [ "${PREFER_MINIKUBE}" -ne 0 ]; then
  # A) direct docker network named "minikube"
  if docker network inspect minikube >/dev/null 2>&1; then
    SELECTED_NETWORK="minikube"
    SELECTED_SUBNET="$(get_network_subnet "minikube")"
    echo "Reusing docker network 'minikube' (subnet: ${SELECTED_SUBNET})" >&2
  fi

  # B) if not found, check for container named like 'minikube' and use its attached network
  if [ -z "${SELECTED_NETWORK}" ]; then
    MK_CONTAINER=$(docker ps -a --format '{{.Names}}' | grep -E '^minikube($|-)' || true)
    if [ -n "${MK_CONTAINER}" ]; then
      MK_CONTAINER=$(echo "$MK_CONTAINER" | head -n1)
      NETS=$(docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}' "$MK_CONTAINER" 2>/dev/null || true)
      NET_NAME=$(echo "$NETS" | awk '{print $1}')
      if [ -n "$NET_NAME" ]; then
        SUBNET=$(get_network_subnet "$NET_NAME")
        if [ -n "$SUBNET" ]; then
          SELECTED_NETWORK="$NET_NAME"
          SELECTED_SUBNET="$SUBNET"
          echo "Found minikube container '$MK_CONTAINER' attached to network '$NET_NAME' (subnet: ${SUBNET}). Reusing." >&2
        fi
      fi
    fi
  fi

  # C) if still not found, and minikube command exists, match networks by minikube ip -> subnet
  if [ -z "${SELECTED_NETWORK}" ] && minikube_exists; then
    MK_IP="$(minikube ip 2>/dev/null || true)"
    if [ -n "$MK_IP" ]; then
      MK_SUBNET_CAND="$(echo "$MK_IP" | awk -F. '{print $1"."$2"."$3".0/24"}')"
      for net in $(docker network ls --format '{{.Name}}'); do
        s=$(get_network_subnet "$net")
        if [ "$s" = "$MK_SUBNET_CAND" ]; then
          SELECTED_NETWORK="$net"
          SELECTED_SUBNET="$s"
          echo "Found docker network '$net' with subnet matching minikube ip (${MK_SUBNET_CAND}). Reusing." >&2
          break
        fi
      done
    fi
  fi
fi

# 2) If a minikube network was found -> export and exit
if [ -n "${SELECTED_NETWORK}" ]; then
  # print exports so caller can eval/source
  echo "export SELECTED_NETWORK_NAME='${SELECTED_NETWORK}'"
  echo "export SELECTED_SUBNET='${SELECTED_SUBNET}'"
  echo "echo \"Using network: \${SELECTED_NETWORK_NAME} (subnet: \${SELECTED_SUBNET})\"" # helpful
  exit 0
fi

# 3) Otherwise: create a new non-overlapping bridge network (tries many /24s)
# Choose starting third octet. If we have MK_IP, start after its third octet to avoid collision.
if [ -n "${MK_IP}" ]; then
  MK_THIRD=$(echo "$MK_IP" | cut -d. -f3)
  START_THIRD=$(((MK_THIRD + 1) % 250))
  [ "$START_THIRD" -lt 2 ] && START_THIRD=2
else
  START_THIRD="$SWARM_SUBNET_OCTET"
fi

for offset in $(seq 0 "${TRIES}"); do
  THIRD=$(((START_THIRD + offset) % 250))
  SUBNET="${BASE_PREFIX}.${THIRD}.0/24"

  CAND_NAME="${TARGET_BASE_NAME}"
  # if target name already exists, check if it matches desired subnet
  if docker network inspect "${CAND_NAME}" >/dev/null 2>&1; then
    EXISTING_SUB=$(get_network_subnet "${CAND_NAME}")
    if [ "${EXISTING_SUB}" = "${SUBNET}" ]; then
      SELECTED_NETWORK="${CAND_NAME}"
      SELECTED_SUBNET="${EXISTING_SUB}"
      echo "Network ${CAND_NAME} already exists and matches subnet ${EXISTING_SUB}. Reusing." >&2
      break
    else
      # name clash with different subnet -> pick a numbered alternative name
      CAND_NAME="${TARGET_BASE_NAME}_${offset}"
    fi
  fi

  # try to create
  if docker network create --driver bridge --subnet "${SUBNET}" "${CAND_NAME}" >/dev/null 2>&1; then
    SELECTED_NETWORK="${CAND_NAME}"
    SELECTED_SUBNET="${SUBNET}"
    echo "Created network ${CAND_NAME} with subnet ${SUBNET}." >&2
    break
  else
    # failed (likely subnet in use) -> continue trying next third octet
    echo "Could not create ${CAND_NAME} with ${SUBNET} (likely overlap). Trying next..." >&2
  fi
done

if [ -z "${SELECTED_NETWORK}" ]; then
  die "Failed to create a non-overlapping network after ${TRIES} attempts."
fi

# 4) Print export lines (so caller can eval the result)
echo "export SELECTED_NETWORK_NAME='${SELECTED_NETWORK}'"
echo "export SELECTED_SUBNET='${SELECTED_SUBNET}'"
export SELECTED_NETWORK_NAME=${SELECTED_NETWORK}
export SELECTED_SUBNET=${SELECTED_SUBNET}
echo "echo \"Using network: \${SELECTED_NETWORK_NAME} (subnet: \${SELECTED_SUBNET})\""

exit 0
