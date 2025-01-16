FROM debian:stable-slim

WORKDIR /gateway

# Missing package for opencv, takes around 500mb
RUN apt-get update

COPY --from=ghcr.io/astral-sh/uv:0.4.3 /uv /bin/uv

COPY ./gateway/*.toml ./

RUN uv sync --compile-bytecode --no-cache

COPY ./preprocessing/run_server.sh ./preprocessing/run_server.sh

EXPOSE 1337

COPY ./gateway.pyy ./gateway.py/

ENTRYPOINT [ "./run_server.sh" ]

