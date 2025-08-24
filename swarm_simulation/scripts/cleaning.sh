#!/bin/bash

docker stop "$(docker ps -aq)"
docker rm "$(docker ps -aq)"
docker network rm "$(docker network ls -q)"

./docker-compose-Adrone.sh
# docker container prune
# docker network prune
