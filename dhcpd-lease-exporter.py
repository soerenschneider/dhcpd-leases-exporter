import os
import re
import sys
import time
import datetime
import argparse

from dataclasses import dataclass

from prometheus_client import start_http_server, write_to_textfile, REGISTRY, CollectorRegistry, Gauge, Counter

pattern = r"lease ([0-9.]+) {.*?starts \d (.*?);.*?ends \d (.*?);.*?hardware ethernet ([:a-f0-9]+);.*?client-hostname \"(.*?)\";.*?}"
regex = re.compile(pattern, re.MULTILINE | re.DOTALL)
default_prefix = "dhcpd_leases"

class PrometheusConfig:
    def __init__(self, textfile=None, port=None): 
        if port and textfile:
            raise ValueError("Can only supply textfile or port, not both")

        if not port and not textfile:
            raise ValueError("Either textfile or port has to be provided")

        self._textfile = textfile
        self._port = port

    @property
    def textfile(self):
        return self._textfile
    
    @textfile.setter
    def textfile(self, value):
        self._textfile = value

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, value: int):
        if not isinstance(value, int):
            raise ValueError("port must be integer")
        if 0 >= value < 65536:
            raise ValueError("port must be in range 0 < port < 65536")
        self._port = value

@dataclass
class Lease:
    mac: str
    ip: str
    name: str
    starts: datetime
    ends: datetime


class DhcpdLeasesExporter:
    def __init__(self, leases_path: str, prom_config: PrometheusConfig, prefix=None):
        if not prom_config:
            raise ValueError("No prometheus config supplied")
        self._prom_config = prom_config

        if not prefix:
            prefix = default_prefix

        if not os.path.exists(leases_path):
            raise ValueError(f"No such file: {leases_path}")
        self._leases_path = leases_path

        if prom_config.textfile:
            self._reg = CollectorRegistry()
        else:
            # use default REGISTRY expose process metrics if the metrics server is used
            self._reg = REGISTRY

        self._metric_lease_start = Gauge(f"{prefix}_lease_start_timestamp", "Lease start timestamp", ["mac", "ip", "name"], registry=self._reg)
        self._metric_lease_end = Gauge(f"{prefix}_lease_end_timestamp", "Lease end timestamp", ["mac", "ip", "name"], registry=self._reg)
        self._metric_entries = Counter(f"{prefix}_leases_total", "Total leases", registry=self._reg)
        self._metric_parse_errors = Counter(f"{prefix}_parsing_errors", "Errors while parsing leases", registry=self._reg)

    @staticmethod
    def parseDate(date: str) -> datetime:
        return datetime.datetime.strptime(date, "%Y/%m/%d %H:%M:%S %Z")

    def scrape(self):
        if self._prom_config.textfile:
            entries = self.parse_file()
            self.write_metrics(entries)
            write_to_textfile(self._prom_config.textfile, self._reg)
        else:
            start_http_server(self._prom_config.port, registry=self._reg)
            while True:
                entries = self.parse_file()
                self.write_metrics(entries)
                time.sleep(30)

    def write_metrics(self, entries):
        for lease in entries:
            ends_unix = lease.ends.strftime("%s")
            self._metric_lease_end.labels(lease.mac, lease.ip, lease.name).set(ends_unix)
            
            starts_unix = lease.starts.strftime("%s")
            self._metric_lease_start.labels(lease.mac, lease.ip, lease.name).set(starts_unix)

            self._metric_entries.inc()

    def parse_file(self):
        leases = list()
        with open(self._leases_path) as f:
            for match in regex.finditer(f.read()):
                if len(match.groups()) < 5:
                    self._metric_parse_errors.inc()
                    return

                ip = match.group(1)
                mac = match.group(4)
                name = match.group(5)
                
                starts = DhcpdLeasesExporter.parseDate(match.group(2))
                ends = DhcpdLeasesExporter.parseDate(match.group(3))

                lease = Lease(ip=ip, mac=mac, name=name, starts=starts, ends=ends)
                leases.append(lease)

        return leases


def parse_args():
    parser = argparse.ArgumentParser(prog="dhcpd-leases-exporter")
    parser.add_argument("-l", "--leases", dest="leases", action="store", required=True)

    promconf = parser.add_mutually_exclusive_group(required=True)
    promconf.add_argument("-p", "--prom-port", action="store", dest="prom_port", type=int)
    promconf.add_argument("-t", "--prom-textfile", action="store", dest="prom_textfile")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    exporter = None
    try:
        conf = PrometheusConfig(port=args.prom_port, textfile=args.prom_textfile)
        exporter = DhcpdLeasesExporter(args.leases, conf)
    except ValueError as e:
        print(f"Invalid config: {str(e)}")
        sys.exit(1)

    exporter.scrape()
