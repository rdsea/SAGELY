FROM debian:stable-slim

WORKDIR /ensemble


COPY --from=ghcr.io/astral-sh/uv:0.4.3 /uv /bin/uv

COPY ./ensemble/*.toml ./


COPY ./ensemble/run_server.sh ./ensemble/run_server.sh

RUN uv sync --compile-bytecode --no-cache

COPY ./ensemble/*.py ./ensemble/

COPY ./ensemble/*.yaml ./ensemble/

COPY ./util/ ./util

EXPOSE 5011

WORKDIR /ensemble/ensemble

ENV PATH="/ensemble/.venv/bin:$PATH"

ENTRYPOINT [ "./run_server.sh" ]
