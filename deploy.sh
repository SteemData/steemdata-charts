#!/bin/bash

docker build -t steemdata-charts .
docker tag steemdata-charts furion/steemdata-charts
docker push furion/steemdata-charts
