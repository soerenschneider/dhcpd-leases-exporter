FROM python:3-slim

WORKDIR /opt/dle
COPY requirements.txt /opt/dle/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY dhcpd_lease_exporter.py /opt/

RUN useradd toor
USER toor

ENV PYTHONPATH /opt/

ENTRYPOINT ["python3", "/opt/dhcpd_lease_exporter.py"]
