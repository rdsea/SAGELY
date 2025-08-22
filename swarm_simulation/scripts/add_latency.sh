#!/bin/bash

# This adds a base delay of 100ms with ±20ms variation.
sudo tc qdisc add dev eth0 root netem delay 100ms 20ms
