integrationtests: venv
	if [ -f output.prom ]; then rm output.prom; fi
	venv/bin/python3 dhcpd_lease_exporter.py -l example.leases -t output.prom
	if [ ! -f output.prom ]; then exit 1; fi
	grep 'dhcpd_leases_lease_start_timestamp{ip="192.168.3.150",mac="aa:bb:cc:dd:ee:ff",name="client-2"}' output.prom
	grep 'dhcpd_leases_lease_start_timestamp{ip="192.168.4.150",mac="ff:ee:dd:cc:bb:aa",name="client-1"}' output.prom
	rm -f output.prom

.PHONY: venv
venv:
	if [ ! -d "venv" ]; then python3 -m venv venv; fi
	venv/bin/pip3 install -r requirements.txt

venv-pylint: venv
	venv/bin/pip3 install pylint pylint-exit anybadge

lint:
	venv/bin/pylint --output-format=text *.py
