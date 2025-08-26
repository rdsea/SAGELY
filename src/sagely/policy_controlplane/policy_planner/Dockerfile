FROM debian:stable-slim

WORKDIR /policy_planner

RUN apt-get update

COPY --from=ghcr.io/astral-sh/uv:0.4.3 /uv /bin/uv

COPY ./policy_planner/*.toml ./

RUN uv sync --compile-bytecode --no-cache

COPY ./policy_planner/run_server.sh ./

COPY ./policy_planner/policy_planner.py ./

EXPOSE 1339

ENV PATH="/policy_planner/.venv/bin:$PATH"

ENTRYPOINT [ "./run_server.sh" ]
