FROM rdsea/debian-slim-opencv:latest

WORKDIR /image_preprocessing/preprocessing

COPY --from=ghcr.io/astral-sh/uv:0.4.3 /uv /bin/uv

COPY ./preprocessing/*.toml ./

RUN uv sync --compile-bytecode --no-cache

WORKDIR /image_preprocessing

COPY ./preprocessing/run_server.sh ./preprocessing/run_server.sh

COPY ./preprocessing/*.yaml ./preprocessing/

COPY ./preprocessing/*.py ./preprocessing/

COPY ./util/ ./util

EXPOSE 5010

WORKDIR /image_preprocessing/preprocessing

ENV PATH="/image_preprocessing/preprocessing/.venv/bin:$PATH"

ENTRYPOINT [ "./run_server.sh" ]

