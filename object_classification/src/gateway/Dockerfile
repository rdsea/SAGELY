FROM debian:stable-slim

WORKDIR /gateway

# Missing package for opencv, takes around 500mb
RUN apt-get update

COPY --from=ghcr.io/astral-sh/uv:0.4.3 /uv /bin/uv

COPY ./gateway/*.toml ./

RUN uv sync --compile-bytecode --no-cache

COPY ./gateway/run_server.sh ./gateway/

COPY ./gateway/gateway.py ./gateway/

EXPOSE 1337

ENV PATH="/gateway/.venv/bin:$PATH"

ENTRYPOINT [ "./run_server.sh" ]

