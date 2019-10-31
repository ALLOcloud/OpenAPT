#!/usr/bin/env bash

docker build . -t openapt
docker run --rm --mount type=bind,source=$PWD,target=/app -w=/app openapt:latest python3.7 setup.py test
