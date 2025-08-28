FROM debian:stable-slim

WORKDIR /policy_coordinator

RUN apt-get update

COPY --from=ghcr.io/astral-sh/uv:0.4.3 /uv /bin/uv

COPY ./policy_coordinator/*.toml ./

RUN uv sync --compile-bytecode --no-cache

COPY ./policy_coordinator/run_server.sh ./

COPY ./policy_coordinator/policy_coordinator.py ./

EXPOSE 1340

ENV PATH="/policy_coordinator/.venv/bin:$PATH"

ENTRYPOINT [ "./run_server.sh" ]



