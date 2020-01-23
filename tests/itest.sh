#!/bin/sh

make venv
python3 dhcpd-lease-exporter.py -l dhcpd.leases -t output.prom
