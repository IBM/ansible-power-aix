# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Copyright (c) IBM
# SPDX-License-Identifier: Apache-2.0
#
# NOTE: Technology Preview
# This EDA event source is provided as a Technology Preview (Beta).
# It is intended for early evaluation and feedback and is not recommended
# for production use. Interfaces/behavior may change in future releases.

DOCUMENTATION = r'''
---
name: aix_cpu_watch
short_description: Watch CPU utilization on AIX hosts over SSH and emit events.
description:
  - Connects to one or more AIX hosts over SSH and samples CPU utilization using
    the C(vmstat) command.
  - Emits an event per host per interval (or only when crossing a threshold).
  - Emits error events on connection/command failures so rules can alert.
version_added: 2.2.0
author:
  - "Nitish K Mishra (@nitismis)"
notes:
  - "Technology Preview (Beta): not production-hardened; behavior and interfaces may change."
  - "Requires network connectivity and SSH access from the rulebook runner to the target AIX hosts."
  - "Uses Paramiko for SSH; ensure the runner environment has the dependency installed."
requirements:
  - "python >= 3.9"
  - "ansible-rulebook"
  - "paramiko"
options:
  hosts:
    description:
      - List of host connection dictionaries.
      - Each entry must include C(host) and may include authentication fields.
    required: true
    type: list
    elements: dict
    suboptions:
      host:
        description: Target AIX host (hostname/IP).
        required: true
        type: str
      username:
        description: SSH username.
        required: false
        type: str
        default: root
      port:
        description: SSH port.
        required: false
        type: int
        default: 22
      key_path:
        description: Path to private key file (on the rulebook runner).
        required: false
        type: str
      password:
        description: SSH password (used if key is not provided/usable).
        required: false
        type: str
      timeout:
        description: SSH command timeout in seconds.
        required: false
        type: int
        default: 10
  interval:
    description: Seconds between samples (applies to the poll loop).
    required: false
    type: int
    default: 10
  threshold:
    description:
      - Threshold percent used to set C(crossed) in emitted events.
      - CPU percent is computed as C(us + sy + wa) from the AIX C(vmstat) output.
    required: false
    type: float
    default: 80.0
  emit_only_above:
    description:
      - If C(true), emit only when computed CPU percent is greater than or equal to C(threshold).
      - If C(false), emit an event every interval and mark C(crossed) accordingly.
    required: false
    type: bool
    default: false
  sample_cmd:
    description:
      - Command used to sample CPU.
      - Default command is suitable for AIX and captures the last C(vmstat) sample line.
    required: false
    type: str
    default: "vmstat 1 2 | tail -1"
'''

EXAMPLES = r'''
- name: CPU watch on a single AIX host (emit every interval)
  hosts: localhost
  sources:
    - ibm.power_aix.aix_cpu_watch:
        hosts:
          - host: "aix1.example.com"
            username: "root"
            key_path: "/home/user/.ssh/id_rsa"
        interval: 10
        threshold: 80.0
        emit_only_above: false
  rules:
    - name: Print CPU events
      condition: event.cpu is defined
      action:
        debug:
          msg: "Host={{ event.host }} CPU={{ event.cpu.percent }} crossed={{ event.crossed }}"

- name: CPU watch on multiple AIX hosts (emit only on threshold crossing)
  hosts: localhost
  sources:
    - ibm.power_aix.aix_cpu_watch:
        hosts:
          - host: "aix1.example.com"
            username: "root"
            key_path: "/home/user/.ssh/id_rsa"
          - host: "aix2.example.com"
            username: "root"
            password: "REDACTED"
        interval: 15
        threshold: 90.0
        emit_only_above: true
  rules:
    - name: Alert when CPU crosses threshold
      condition: event.cpu is defined and event.crossed == true
      action:
        debug:
          msg: "ALERT: {{ event.host }} CPU {{ event.cpu.percent }}% (thr={{ event.threshold }})"

- name: Handle errors (always emitted)
  hosts: localhost
  sources:
    - ibm.power_aix.aix_cpu_watch:
        hosts:
          - host: "aix-bad.example.com"
            username: "root"
            key_path: "/home/user/.ssh/id_rsa"
  rules:
    - name: Notify on source errors
      condition: event.error is defined
      action:
        debug:
          msg: "ERROR from {{ event.host }}: {{ event.error }}"
'''

RETURN = r'''
timestamp:
  description: UTC timestamp in ISO 8601 format.
  type: str
  returned: always
host:
  description: Hostname/IP for which the event was generated.
  type: str
  returned: always
cpu:
  description: CPU metrics (present for successful samples).
  type: dict
  returned: when successful
  contains:
    percent:
      description: Computed CPU usage percent (us + sy + wa).
      type: float
    us:
      description: User CPU percent from vmstat.
      type: float
    sy:
      description: System CPU percent from vmstat.
      type: float
    id:
      description: Idle CPU percent from vmstat.
      type: float
    wa:
      description: IO wait percent from vmstat.
      type: float
threshold:
  description: Threshold used to compute crossed.
  type: float
  returned: when cpu is present
crossed:
  description: True if cpu.percent >= threshold, else False.
  type: bool
  returned: when cpu is present
error:
  description: Error message if polling failed for the host.
  type: str
  returned: on error
severity:
  description: Severity of error events.
  type: str
  returned: on error
source:
  description: Source identifier.
  type: str
  returned: always
'''

from ansible_rulebook.source import Source
import asyncio
from datetime import datetime, timezone
import paramiko
from typing import List, Dict, Any, Optional


def _compute_cpu_usage_from_vmstat(line: str) -> Dict[str, float]:
    """
    AIX vmstat last 4 columns are: us sy id wa
    We'll parse the last 4 numeric fields and compute:
      usage = us + sy + wa
    """
    toks = [t for t in line.strip().split() if t.replace('.', '', 1).isdigit()]
    if len(toks) < 4:
        raise ValueError(f"Unexpected vmstat output: {line!r}")
    us, sy, idl, wa = map(float, toks[-4:])
    usage = us + sy + wa  # 100 - idle
    return {"us": us, "sy": sy, "id": idl, "wa": wa, "usage": usage}


class _SSHClient:
    def __init__(self, host: str, username: str, port: int = 22,
                 key_path: Optional[str] = None, password: Optional[str] = None,
                 timeout: int = 10):
        self.host = host
        self.username = username
        self.port = port
        self.key_path = key_path
        self.password = password
        self.timeout = timeout
        self._client = None

    def connect(self):
        if self._client:
            return
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pkey = None
        if self.key_path:
            try:
                pkey = paramiko.RSAKey.from_private_key_file(self.key_path)
            except Exception:
                # Try ECDSA if RSA fails
                try:
                    pkey = paramiko.ECDSAKey.from_private_key_file(self.key_path)
                except Exception:
                    pkey = None
        self._client.connect(
            self.host,
            port=self.port,
            username=self.username,
            password=self.password if not pkey else None,
            pkey=pkey,
            look_for_keys=False,
            allow_agent=True,
            timeout=self.timeout,
        )

    def run(self, cmd: str) -> str:
        if not self._client:
            self.connect()
        stdin, stdout, stderr = self._client.exec_command(cmd, timeout=self.timeout)
        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")
        if err and not out:
            # vmstat prints headers to stdout; non-empty err with empty out is suspicious
            raise RuntimeError(f"Command error on {self.host}: {err.strip()}")
        return out

    def close(self):
        try:
            if self._client:
                self._client.close()
        finally:
            self._client = None


@Source(name="aix_cpu_watch")
class AIXCPUWatch:
    """
    EDA event source: aix_cpu_watch
    """
    def __init__(self):
        self.clients: Dict[str, _SSHClient] = {}
        self.running = True

    async def run(self, queue, args):
        hosts: List[Dict[str, Any]] = args.get("hosts", [])
        if not hosts:
            raise ValueError("AIXCPUWatch: 'hosts' list is required.")

        interval = int(args.get("interval", 10))
        threshold = float(args.get("threshold", 80.0))
        emit_only_above = bool(args.get("emit_only_above", False))
        sample_cmd = args.get("sample_cmd", "vmstat 1 2 | tail -1")

        # Prepare SSH clients
        for h in hosts:
            key = h["host"]
            self.clients[key] = _SSHClient(
                host=h["host"],
                username=h.get("username", "root"),
                port=int(h.get("port", 22)),
                key_path=h.get("key_path"),
                password=h.get("password"),
                timeout=int(h.get("timeout", 10)),
            )

        try:
            while self.running:
                start = asyncio.get_event_loop().time()

                async def poll_one(h: Dict[str, Any]):
                    host = h["host"]
                    cli = self.clients[host]
                    try:
                        # Run vmstat once per cycle
                        out = await asyncio.to_thread(cli.run, sample_cmd)
                        # Use the last non-empty line (tail -1 already, but be safe)
                        lines = [line for line in out.splitlines() if line.strip()][-1]
                        if not lines:
                            raise ValueError("vmstat returned no data")
                        cpu = _compute_cpu_usage_from_vmstat(lines)
                        crossed = cpu["usage"] >= threshold
                        if (not emit_only_above) or crossed:
                            event = {
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "host": host,
                                "cpu": {
                                    "percent": round(cpu["usage"], 2),
                                    "us": cpu["us"],
                                    "sy": cpu["sy"],
                                    "id": cpu["id"],
                                    "wa": cpu["wa"],
                                },
                                "threshold": threshold,
                                "crossed": crossed,
                                "source": "aix_cpu_watch",
                            }
                            await queue.put(event)
                    except Exception as e:
                        err_event = {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "host": host,
                            "error": str(e),
                            "source": "aix_cpu_watch",
                            "severity": "error",
                        }
                        # Always emit errors so rules can alert
                        await queue.put(err_event)

                # Poll all hosts concurrently
                await asyncio.gather(*(poll_one(h) for h in hosts))

                # Sleep until next tick (interval from loop start)
                elapsed = asyncio.get_event_loop().time() - start
                await asyncio.sleep(max(0, interval - elapsed))
        finally:
            # Cleanup SSH sessions
            for cli in self.clients.values():
                cli.close()
