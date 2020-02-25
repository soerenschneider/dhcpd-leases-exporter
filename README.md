# dhcpd-leases-exporter
Prometheus exporter for a [leases db file](https://man.openbsd.org/dhclient.leases.5) created by dhcpd. 

## usage

```
usage: dhcpd-leases-exporter [-h] -l LEASES (-p PROM_PORT | -t PROM_TEXTFILE)
dhcpd-leases-exporter: error: the following arguments are required: -l/--leases
```

Metrics can be either parsed continously and scraped from a web endpoint or be written 
as a prometheus text file, exported by a node_exporter. 

## exported metrics

```
# HELP dhcpd_leases_lease_start_timestamp Lease start timestamp
# TYPE dhcpd_leases_lease_start_timestamp gauge
dhcpd_leases_lease_start_timestamp{ip="192.168.4.150",mac="ff:ee:dd:cc:bb:aa",name="client-1"} 1.579641109e+09
dhcpd_leases_lease_start_timestamp{ip="192.168.3.150",mac="aa:bb:cc:dd:ee:ff",name="client-2"} 1.579710352e+09
# HELP dhcpd_leases_lease_end_timestamp Lease end timestamp
# TYPE dhcpd_leases_lease_end_timestamp gauge
dhcpd_leases_lease_end_timestamp{ip="192.168.4.150",mac="ff:ee:dd:cc:bb:aa",name="client-1"} 1.579684309e+09
dhcpd_leases_lease_end_timestamp{ip="192.168.3.150",mac="aa:bb:cc:dd:ee:ff",name="client-2"} 1.579753552e+09
# HELP dhcpd_leases_leases_total Total leases
# TYPE dhcpd_leases_leases_total counter
dhcpd_leases_leases_total 2.0
# TYPE dhcpd_leases_leases_created gauge
dhcpd_leases_leases_created 1.5798196373855052e+09
# HELP dhcpd_leases_parsing_errors_total Errors while parsing leases
# TYPE dhcpd_leases_parsing_errors_total counter
dhcpd_leases_parsing_errors_total 0.0
# TYPE dhcpd_leases_parsing_errors_created gauge
dhcpd_leases_parsing_errors_created 1.5798196373855207e+09
```