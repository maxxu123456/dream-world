#!/usr/bin/env python3
"""Check the DS-facing Game Sync services while the website awaits tuck-in."""

import os
import socket
from pathlib import Path

from dnslib import DNSRecord, QTYPE


def listening_tcp_ports() -> set[int]:
    ports: set[int] = set()
    for table_path in (Path("/proc/net/tcp"), Path("/proc/net/tcp6")):
        if not table_path.exists():
            continue
        for line in table_path.read_text().splitlines()[1:]:
            fields = line.split()
            if len(fields) >= 4 and fields[3] == "0A":  # TCP_LISTEN
                ports.add(int(fields[1].rsplit(":", 1)[1], 16))
    return ports


required_tcp_ports = {80, 443, 29900}
missing_ports = required_tcp_ports - listening_tcp_ports()
if missing_ports:
    raise SystemExit(f"Game Sync TCP listeners missing: {sorted(missing_ports)}")

query = DNSRecord.question("conntest.nintendowifi.net", "A")
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as dns_socket:
    dns_socket.settimeout(3)
    dns_socket.sendto(query.pack(), ("127.0.0.1", 53))
    response_data, _ = dns_socket.recvfrom(4096)

response = DNSRecord.parse(response_data)
expected_ip = os.environ["HOST_IP"]
answers = {
    str(record.rdata)
    for record in response.rr
    if QTYPE.get(record.rtype) == "A"
}
if expected_ip not in answers:
    raise SystemExit(f"DNS returned {sorted(answers)}, expected {expected_ip}")
