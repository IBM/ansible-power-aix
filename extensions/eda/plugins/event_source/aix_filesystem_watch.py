
from __future__ import annotations

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Copyright (c) IBM
# SPDX-License-Identifier: Apache-2.0
#

# pylint: disable=duplicate-code

import asyncio
from datetime import datetime, timezone
from typing import Any

import paramiko  # pylint: disable=import-error

DOCUMENTATION = r"""
---
name: aix_filesystem_watch
short_description: Watch filesystem utilization on AIX hosts over SSH and emit events.
description:
  - Connects to one or more AIX hosts over SSH and samples filesystem utilization using
    the C(df) command.
  - Emits an event per host per filesystem per interval (or only when crossing a threshold).
  - Emits error events on connection/command failures so rules can alert.
version_added: 2.2.0
author:
  - "Shreyansh Chamola(@schamola)"
notes:
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
    default: 60
  threshold:
    description:
      - Threshold percentage used to set C(crossed) in emitted events.
      - Filesystem usage percent is computed from the AIX C(df) output.
    required: false
    type: float
    default: 80.0
  emit_only_above:
    description:
      - If C(true), emit only when filesystem usage percent is greater than or equal to C(threshold).
      - If C(false), emit an event every interval and mark C(crossed) accordingly.
    required: false
    type: bool
    default: false
  filesystems:
    description:
      - List of specific filesystems to monitor (e.g., ["/", "/home", "/var"]).
      - If not specified, monitors all mounted filesystems.
    required: false
    type: list
    elements: str
  sample_cmd:
    description:
      - Command used to sample filesystem usage.
      - Default command is suitable for AIX and captures filesystem statistics.
    required: false
    type: str
    default: "df -g"
"""

EXAMPLES = r"""
- name: Filesystem watch on a single AIX host (emit every interval)
  hosts: localhost
  sources:
    - ibm.power_aix.aix_filesystem_watch:
        hosts:
          - host: "aix1.example.com"
            username: "root"
            key_path: "/home/user/.ssh/id_rsa"
        interval: 60
        threshold: 80.0
        emit_only_above: false
  rules:
    - name: Print filesystem events
      condition: event.filesystem is defined
      action:
        debug:
          msg: "Host={{ event.host }} FS={{ event.filesystem.mount }} Usage={{ event.filesystem.percent }}% crossed={{ event.crossed }}"

- name: Filesystem watch on multiple AIX hosts (emit only on threshold crossing)
  hosts: localhost
  sources:
    - ibm.power_aix.aix_filesystem_watch:
        hosts:
          - host: "aix1.example.com"
            username: "root"
            key_path: "/home/user/.ssh/id_rsa"
          - host: "aix2.example.com"
            username: "root"
            password: "REDACTED"
        interval: 120
        threshold: 90.0
        emit_only_above: true
        filesystems:
          - "/"
          - "/home"
          - "/var"
  rules:
    - name: Alert when filesystem crosses threshold
      condition: event.filesystem is defined and event.crossed == true
      action:
        debug:
          msg: "ALERT: {{ event.host }} FS {{ event.filesystem.mount }} at {{ event.filesystem.percent }}% (thr={{ event.threshold }})"

- name: Handle errors (always emitted)
  hosts: localhost
  sources:
    - ibm.power_aix.aix_filesystem_watch:
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
"""

RETURN = r"""
timestamp:
  description: UTC timestamp in ISO 8601 format.
  type: str
  returned: always
host:
  description: Hostname/IP for which the event was generated.
  type: str
  returned: always
filesystem:
  description: Filesystem metrics (present for successful samples).
  type: dict
  returned: when successful
  contains:
    mount:
      description: Filesystem mount point.
      type: str
    device:
      description: Device name.
      type: str
    percent:
      description: Filesystem usage percentage.
      type: float
    size_gb:
      description: Total filesystem size in GB.
      type: float
    used_gb:
      description: Used space in GB.
      type: float
    free_gb:
      description: Free space in GB.
      type: float
    threshold:
      description: Threshold used to compute crossed.
      type: float
      returned: when filesystem is present
    crossed:
      description: True if filesystem.percent >= threshold, else False.
      type: bool
      returned: when filesystem is present
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
"""


def _parse_df_output(output: str, filter_filesystems: list[str] | None = None) -> list[dict[str, Any]]:
    """Parse AIX df -g output and extract filesystem information.

    AIX df -g output format:
    Filesystem    GB blocks      Free %Used    Iused %Iused Mounted on
    /dev/hd4           2.00      1.50   25%     5120    10% /
    /dev/hd2          10.00      3.50   65%    15000    15% /usr

    Returns list of filesystem dictionaries with usage information.
    """
    filesystems = []
    lines = output.strip().split("\n")

    # Skip header line
    for line in lines[1:]:
        if not line.strip():
            continue

        # Parse df output - handle potential whitespace variations
        parts = line.split()
        min_parts_required = 7
        if len(parts) < min_parts_required:
            continue

        device = parts[0]
        mount = parts[6]

        # Skip if filtering and mount not in list
        if filter_filesystems and mount not in filter_filesystems:
            continue

        try:
            size_gb = float(parts[1])
            free_gb = float(parts[2])
            used_percent_str = parts[3].rstrip("%")
            used_percent = float(used_percent_str)
            used_gb = size_gb - free_gb

            filesystems.append({
                "device": device,
                "mount": mount,
                "size_gb": round(size_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "percent": round(used_percent, 2),
            })
        except (ValueError, IndexError):
            # Skip lines that don't parse correctly
            continue

    return filesystems


class _SSHClient:  # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        host: str,
        username: str,
        port: int = 22,
        key_path: str | None = None,
        password: str | None = None,
        timeout: int = 10,
    ) -> None:
        self.host = host
        self.username = username
        self.port = port
        self.key_path = key_path
        self.password = password
        self.timeout = timeout
        self._client = None

    def connect(self) -> None:
        if self._client:
            return
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        pkey = None
        if self.key_path:
            try:
                pkey = paramiko.RSAKey.from_private_key_file(self.key_path)
            except (paramiko.SSHException, OSError):
                # Try ECDSA if RSA fails
                try:
                    pkey = paramiko.ECDSAKey.from_private_key_file(self.key_path)
                except (paramiko.SSHException, OSError):
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
        _stdin, stdout, stderr = self._client.exec_command(cmd, timeout=self.timeout)
        out = stdout.read().decode(errors="ignore")
        err = stderr.read().decode(errors="ignore")
        if err and not out:
            msg = f"Command error on {self.host}: {err.strip()}"
            raise RuntimeError(msg)
        return out

    def close(self) -> None:
        try:
            if self._client:
                self._client.close()
        finally:
            self._client = None


def _create_ssh_clients(hosts: list[dict[str, Any]]) -> dict[str, _SSHClient]:
    """Create SSH clients for all hosts.

    Args:
        hosts: List of host configuration dictionaries

    Returns:
        Dictionary mapping host to SSH client

    """
    clients = {}
    for h in hosts:
        key = h["host"]
        clients[key] = _SSHClient(
            host=h["host"],
            username=h.get("username", "root"),
            port=int(h.get("port", 22)),
            key_path=h.get("key_path"),
            password=h.get("password"),
            timeout=int(h.get("timeout", 10)),
        )
    return clients


async def _poll_host(  # pylint: disable=too-many-positional-arguments
    host_config: dict[str, Any],
    client: _SSHClient,
    queue: asyncio.Queue,
    sample_cmd: str,
    filter_filesystems: list[str] | None,
    threshold: float,
    *,
    emit_only_above: bool,
) -> None:
    """Poll a single host for filesystem usage.

    Args:
        host_config: Host configuration dictionary
        client: SSH client for the host
        queue: Queue to send events to
        sample_cmd: Command to run for sampling
        filter_filesystems: List of filesystems to filter
        threshold: Threshold percentage
        emit_only_above: Whether to emit only above threshold

    """
    host = host_config["host"]

    def _validate_filesystems(filesystems: list) -> None:
        """Validate that filesystems were returned.

        Args:
            filesystems: List of filesystem data

        Raises:
            ValueError: If no filesystems were returned

        """
        if not filesystems:
            msg = "No filesystem data returned or no filesystems match filter"
            raise ValueError(msg)

    try:
        # Run df command
        out = await asyncio.to_thread(client.run, sample_cmd)
        filesystems = _parse_df_output(out, filter_filesystems)
        _validate_filesystems(filesystems)

        # Emit event for each filesystem
        for fs in filesystems:
            crossed = fs["percent"] >= threshold
            if (not emit_only_above) or crossed:
                event = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "host": host,
                    "filesystem": {
                        "mount": fs["mount"],
                        "device": fs["device"],
                        "percent": fs["percent"],
                        "size_gb": fs["size_gb"],
                        "used_gb": fs["used_gb"],
                        "free_gb": fs["free_gb"],
                    },
                    "threshold": threshold,
                    "crossed": crossed,
                    "source": "aix_filesystem_watch",
                }
                await queue.put(event)
    except (ValueError, RuntimeError, OSError) as e:
        err_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "host": host,
            "error": str(e),
            "source": "aix_filesystem_watch",
            "severity": "error",
        }
        # Always emit errors so rules can alert
        await queue.put(err_event)


async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    """EDA event source: aix_filesystem_watch.

    Main entry point for the event source plugin.
    """
    hosts: list[dict[str, Any]] = args.get("hosts", [])
    if not hosts:
        msg = "AIXFilesystemWatch: 'hosts' list is required."
        raise ValueError(msg)

    interval = int(args.get("interval", 60))
    threshold = float(args.get("threshold", 80.0))
    emit_only_above = bool(args.get("emit_only_above", False))
    sample_cmd = args.get("sample_cmd", "df -g")
    filter_filesystems = args.get("filesystems")

    # Prepare SSH clients
    clients = _create_ssh_clients(hosts)

    try:
        while True:
            start = asyncio.get_event_loop().time()

            # Poll all hosts concurrently
            await asyncio.gather(*(
                _poll_host(h, clients[h["host"]], queue, sample_cmd, filter_filesystems, threshold, emit_only_above=emit_only_above)
                for h in hosts
            ))

            # Sleep until next tick (interval from loop start)
            elapsed = asyncio.get_event_loop().time() - start
            await asyncio.sleep(max(0, interval - elapsed))
    finally:
        # Cleanup SSH sessions
        for cli in clients.values():
            cli.close()
