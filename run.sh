#!/bin/sh
while [ true ]
do
    python Charts.py
    python MarketCap.py
    sleep 40000
done
