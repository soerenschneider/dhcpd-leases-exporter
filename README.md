# dhcpd-leases-exporter
Prometheus exporter for a [leases db file](https://man.openbsd.org/dhclient.leases.5) created by dhcpd. 

## usage

```
usage: dhcpd-leases-exporter [-h] -l LEASES (-p PROM_PORT | -t PROM_TEXTFILE)
dhcpd-leases-exporter: error: the following arguments are required: -l/--leases
```

Metrics can be either parsed continously and scraped from a web endpoint or be written 
as a prometheus text file, exported by a node_exporter. 
