#!/bin/bash

LOCAL_PORT=8910


# Run the webserver
docker run --rm -it -p ${LOCAL_PORT}:5000 --env-file config.env trafikkmeldinger
