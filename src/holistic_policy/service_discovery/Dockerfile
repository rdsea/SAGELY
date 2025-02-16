FROM debian:stable-slim

WORKDIR /service_discovery

# Missing package for opencv, takes around 500mb
RUN apt-get update

COPY --from=ghcr.io/astral-sh/uv:0.4.3 /uv /bin/uv

COPY ./service_discovery/*.toml ./

RUN uv sync --compile-bytecode --no-cache

COPY ./service_discovery/run_server.sh ./

COPY ./service_discovery/service_discovery.py ./

EXPOSE 1337

ENV PATH="/service_discovery/.venv/bin:$PATH"

ENTRYPOINT [ "./run_server.sh" ]

