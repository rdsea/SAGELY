FROM debian:stable-slim

WORKDIR /context_management

RUN apt-get update

COPY --from=ghcr.io/astral-sh/uv:0.4.3 /uv /bin/uv

COPY ./context_management/*.toml ./

RUN uv sync --compile-bytecode --no-cache

COPY ./context_management/run_server.sh ./

COPY ./context_management/context_management.py ./

EXPOSE 1338

ENV PATH="/context_management/.venv/bin:$PATH"

ENTRYPOINT [ "./run_server.sh" ]

