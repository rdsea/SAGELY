FROM debian:stable-slim

WORKDIR /policy_change_management

RUN apt-get update

COPY --from=ghcr.io/astral-sh/uv:0.4.3 /uv /bin/uv

COPY ./policy_change_management/*.toml ./

RUN uv sync --compile-bytecode --no-cache

COPY ./policy_change_management/run_server.sh ./

COPY ./policy_change_management/policy_change_management.py ./

EXPOSE 1341

ENV PATH="/policy_change_management/.venv/bin:$PATH"

ENTRYPOINT [ "./run_server.sh" ]


