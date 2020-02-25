import os
import re
import sys
import time
import datetime
import argparse

from dataclasses import dataclass

from prometheus_client import start_http_server, write_to_textfile, REGISTRY, CollectorRegistry, Gauge, Counter

PATTERN = r"lease ([0-9.]+) {.*?starts \d (.*?);.*?ends \d (.*?);.*?hardware ethernet ([:a-f0-9]+);.*?client-hostname \"(.*?)\";.*?}"
REGEX = re.compile(PATTERN, re.MULTILINE | re.DOTALL)
DEFAULT_PREFIX = "dhcpd_leases"


class PrometheusConfig:
    def __init__(self, textfile=None, port=None): 
        if port and textfile:
            raise ValueError("Can only supply textfile or port, not both")

        if not port and not textfile:
            raise ValueError("Either textfile or port has to be provided")

        self._textfile = textfile
        self._port = port

        if textfile:
            self.reg = CollectorRegistry()
        else:
            # use default REGISTRY expose process metrics if the metrics server is used
            self.reg = REGISTRY
            start_http_server(self._port, registry=self.reg)


    def persist_metrics(self):
        if self._textfile:
            write_to_textfile(self._textfile, self.reg)

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
            prefix = DEFAULT_PREFIX

        self._metric_lease_start = Gauge(f"{prefix}_lease_start_timestamp", "Lease start timestamp", ["mac", "ip", "name"], registry=prom_config.reg)
        self._metric_lease_end = Gauge(f"{prefix}_lease_end_timestamp", "Lease end timestamp", ["mac", "ip", "name"], registry=prom_config.reg)
        self._metric_entries = Counter(f"{prefix}_leases_total", "Total leases", registry=prom_config.reg)
        self._metric_parse_errors = Counter(f"{prefix}_parsing_errors", "Errors while parsing leases", registry=prom_config.reg)

        if not os.path.exists(leases_path):
            raise ValueError(f"No such file: {leases_path}")
        self._leases_path = leases_path

    @staticmethod
    def parseDate(date: str) -> datetime:
        return datetime.datetime.strptime(date, "%Y/%m/%d %H:%M:%S %Z")

    def scrape(self):
        if self._prom_config.textfile:
            entries = self.parse_file()
            self._prom_config.persist_metrics()
        else:
            while True:
                entries = self.parse_file()
                time.sleep(30)

    def parse_file(self) -> list:
        leases = list()
        with open(self._leases_path) as f:
            for match in REGEX.finditer(f.read()):
                if len(match.groups()) < 5:
                    self._metric_parse_errors.inc()
                    return
                
                starts = DhcpdLeasesExporter.parseDate(match.group(2))
                ends = DhcpdLeasesExporter.parseDate(match.group(3))
                
                lease = Lease(ip=match.group(1), mac=match.group(4), name=match.group(5), starts=starts, ends=ends)

                ends_unix = lease.ends.strftime("%s")
                self._metric_lease_end.labels(lease.mac, lease.ip, lease.name).set(ends_unix)
                
                starts_unix = lease.starts.strftime("%s")
                self._metric_lease_start.labels(lease.mac, lease.ip, lease.name).set(starts_unix)

                self._metric_entries.inc()

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
