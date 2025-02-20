FROM debian:stable-slim

WORKDIR /context

# Missing package for opencv, takes around 500mb
RUN apt-get update

COPY --from=ghcr.io/astral-sh/uv:0.4.3 /uv /bin/uv

COPY ./context/*.toml ./

RUN uv sync --compile-bytecode --no-cache

COPY ./context/run_server.sh ./

COPY ./context/context.py ./

EXPOSE 1338

ENV PATH="/context/.venv/bin:$PATH"

ENTRYPOINT [ "./run_server.sh" ]

