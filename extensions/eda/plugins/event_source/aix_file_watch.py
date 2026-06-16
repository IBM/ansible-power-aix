# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Copyright (c) IBM
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import asyncio
from datetime import datetime, timezone
import paramiko
from typing import Any

DOCUMENTATION = r"""
---
name: aix_file_watch
short_description: Watch file content modifications on AIX hosts over SSH and emit events.
description:
  - Connects to one or more AIX hosts over SSH and monitors file content changes.
  - Uses AIX csum command (MD5) to detect content modifications.
  - Detects changes in file permissions, ownership, and size.
  - Emits events when monitored files are modified.
  - Emits error events on connection/command failures so rules can alert.
version_added: 2.2.0
author:
  - AIX Development Team (@vivekpandeyibm)
notes:
  - "Requires network connectivity and SSH access from the rulebook runner to the target AIX hosts."
  - "Uses Paramiko for SSH; ensure the runner environment has the dependency installed."
  - "Uses AIX csum command (MD5) for checksums."
  - "Tracks file permissions, ownership, and size changes in addition to content."
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
  files:
    description:
      - List of files to monitor for content changes.
      - Each file path should be absolute path on the target AIX host.
    required: true
    type: list
    elements: str
  interval:
    description: Seconds between file checks (applies to the poll loop).
    required: false
    type: int
    default: 30
  emit_initial:
    description:
      - If C(true), emit initial events for all monitored files on startup.
      - If C(false), only emit events when files actually change.
    required: false
    type: bool
    default: false
"""

EXAMPLES = r"""
- name: Monitor critical system files on AIX
  hosts: localhost
  sources:
    - ibm.power_aix.aix_file_watch:
        hosts:
          - host: "aix1.example.com"
            username: "root"
            key_path: "/home/user/.ssh/id_rsa"
        files:
          - "/etc/passwd"
          - "/etc/ssh/sshd_config"
          - "/etc/sudoers"
        interval: 60
        emit_initial: false
  rules:
    - name: Alert on file modifications
      condition: event.file is defined and event.changed == true
      action:
        debug:
          msg: "File {{ event.file }} modified on {{ event.host }} at {{ event.timestamp }}"

- name: Alert on permission changes
  hosts: localhost
  sources:
    - ibm.power_aix.aix_file_watch:
        hosts:
          - host: "aix1.example.com"
            username: "root"
            key_path: "/home/user/.ssh/id_rsa"
        files:
          - "/etc/passwd"
        interval: 30
  rules:
    - name: Security alert on permission changes
      condition: event.changes is defined and "permissions" in event.changes
      action:
        debug:
          msg: "SECURITY ALERT: {{ event.file }} permissions changed from {{ event.previous_permissions }} to {{ event.file_mode }}"
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
file:
  description: Full path of the monitored file.
  type: str
  returned: when successful
action:
  description: Type of action detected (created, modified, deleted, initial).
  type: str
  returned: when successful
changed:
  description: True if file content actually changed, False for initial scan.
  type: bool
  returned: when successful
changes:
  description: List of what changed (content, permissions, owner, size).
  type: list
  returned: when file was modified
checksum:
  description: MD5 checksum of the file content.
  type: str
  returned: when file exists
previous_checksum:
  description: Previous MD5 checksum (only for modifications).
  type: str
  returned: when file content was modified
file_size:
  description: Size of the file in bytes.
  type: int
  returned: when file exists
previous_size:
  description: Previous file size in bytes.
  type: int
  returned: when file size changed
file_mode:
  description: File permissions in octal format.
  type: str
  returned: when file exists
previous_permissions:
  description: Previous file permissions.
  type: str
  returned: when permissions changed
file_owner:
  description: File owner (user:group).
  type: str
  returned: when file exists
previous_owner:
  description: Previous file owner.
  type: str
  returned: when owner changed
error:
  description: Error message if monitoring failed for the host/file.
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


def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format for event timestamping.

    Args:
        None

    Note:
        Uses timezone-aware datetime for consistency.

    Returns:
        str: ISO 8601 timestamp (e.g., '2026-04-01T06:54:42.123456+00:00')
    """
    return datetime.now(timezone.utc).isoformat()


def load_ssh_key(key_path: str | None) -> paramiko.PKey | None:
    """Load SSH private key from file for authentication to AIX hosts.

    Tries RSA format first, then ECDSA format.

    Args:
        key_path: Path to the private key file

    Note:
        Returns None if key cannot be loaded. Does not raise exceptions.

    Returns:
        paramiko.PKey or None: Loaded private key object, or None if failed
    """
    if not key_path:
        return None

    # Try RSA key
    try:
        return paramiko.RSAKey.from_private_key_file(key_path)
    except (paramiko.SSHException, OSError):
        # Try ECDSA if RSA fails
        try:
            return paramiko.ECDSAKey.from_private_key_file(key_path)
        except (paramiko.SSHException, OSError):
            return None

    return None


def create_ssh_client(host_info: dict[str, Any]) -> paramiko.SSHClient:
    """Create and establish SSH connection to a remote AIX host using Paramiko.

    Handles both key-based and password-based authentication.

    Args:
        host_info: Connection parameters (host, username, port, key_path, password, timeout)

    Note:
        Prefers key-based auth over password. Raises exceptions on failure.

    Returns:
        paramiko.SSHClient: Connected SSH client object
    """
    # Extract connection details
    hostname = host_info["host"]
    username = host_info.get("username", "root")
    port = int(host_info.get("port", 22))
    key_path = host_info.get("key_path")
    password = host_info.get("password")
    timeout = int(host_info.get("timeout", 10))

    # Create SSH client
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Load private key if provided
    private_key = load_ssh_key(key_path)

    # Connect to host
    client.connect(
        hostname,
        port=port,
        username=username,
        password=password if not private_key else None,
        pkey=private_key,
        look_for_keys=False,
        allow_agent=True,
        timeout=timeout,
    )

    return client


def get_file_checksum(ssh_client: paramiko.SSHClient, file_path: str) -> str:
    """Calculate MD5 checksum of a file using the AIX-native csum command.

    Used to detect content changes in monitored files.

    Args:
        ssh_client: Active SSH connection to the AIX host
        file_path: Absolute path to the file on the remote AIX system

    Note:
        Returns "unknown" on failure rather than raising exceptions.

    Returns:
        str: MD5 checksum string, or "unknown" if command failed
    """
    # Use AIX csum command (MD5)
    _stdin, stdout, stderr = ssh_client.exec_command(f"csum '{file_path}' 2>/dev/null")
    output = stdout.read().decode(errors="ignore").strip()

    if output and not stderr.read():
        return output.split()[0]

    return "unknown"


def get_file_info(ssh_client: paramiko.SSHClient, file_path: str) -> dict[str, Any]:
    """Get complete file information including checksum, permissions, ownership, and size.

    Uses ls -la for file attributes and csum for content checksum.

    Args:
        ssh_client: Active SSH connection to the AIX host
        file_path: Absolute path to the file on the remote AIX system

    Note:
        Returns exists=False if file doesn't exist or parsing fails.

    Returns:
        dict: File info (exists, checksum, permissions, owner, size, error)
    """
    try:
        # Check if file exists
        _stdin, stdout, _stderr = ssh_client.exec_command(f"ls -la '{file_path}' 2>/dev/null")
        ls_output = stdout.read().decode(errors="ignore").strip()

        if not ls_output:
            return {"exists": False}

        # Parse ls output
        parts = ls_output.split()
        ls_output_min_parts = 9
        if len(parts) >= ls_output_min_parts:
            permissions = parts[0]
            owner = f"{parts[2]}:{parts[3]}"
            size = int(parts[4]) if parts[4].isdigit() else 0
        else:
            permissions = "unknown"
            owner = "unknown:unknown"
            size = 0

        # Get checksum
        checksum = get_file_checksum(ssh_client, file_path)

    except (OSError, ValueError) as e:
        return {"exists": False, "error": str(e)}
    else:
        return {
            "exists": True,
            "checksum": checksum,
            "permissions": permissions,
            "owner": owner,
            "size": size,
        }


def detect_changes(
    current_info: dict[str, Any],
    previous_info: dict[str, Any] | None,
) -> list[str]:
    """Compare current and previous file information to detect what changed.

    Identifies changes in content, permissions, owner, and size.

    Args:
        current_info: Current file information from get_file_info()
        previous_info: Previous file information, or None for new files

    Note:
        Returns ["created"] if previous_info is None.

    Returns:
        list: Change types ("created", "content", "permissions", "owner", "size")
    """
    if previous_info is None:
        return ["created"]

    changes = []

    # Check content change
    if current_info["checksum"] != previous_info["checksum"]:
        changes.append("content")

    # Check permission change
    if current_info["permissions"] != previous_info["permissions"]:
        changes.append("permissions")

    # Check owner change
    if current_info["owner"] != previous_info["owner"]:
        changes.append("owner")

    # Check size change
    if current_info["size"] != previous_info["size"]:
        changes.append("size")

    return changes


def create_file_event(
    hostname: str,
    file_path: str,
    action: str,
    current_info: dict[str, Any],
    previous_info: dict[str, Any] | None,
    changes: list[str],
) -> dict[str, Any]:
    """Create a standardized event dictionary for file changes to be emitted to the rulebook.

    Formats all file change information into a consistent structure for EDA rules.

    Args:
        hostname: Hostname or IP of the AIX system where change occurred
        file_path: Absolute path to the changed file
        action: Type of action ("initial", "created", "modified")
        current_info: Current file information from get_file_info()
        previous_info: Previous file information, or None for new files
        changes: List of change types from detect_changes()

    Note:
        Sets changed=False for "initial" action. Includes previous values when changed.

    Returns:
        dict: Event with timestamp, host, file, action, changes, and file metadata
    """
    event = {
        "timestamp": get_current_timestamp(),
        "host": hostname,
        "file": file_path,
        "action": action,
        "changed": action != "initial",
        "source": "aix_file_watch",
    }

    # Add what changed
    if changes:
        event["changes"] = changes

    # Add current file info
    event["checksum"] = current_info["checksum"]
    event["file_size"] = current_info["size"]
    event["file_mode"] = current_info["permissions"]
    event["file_owner"] = current_info["owner"]

    # Add previous values if they exist
    if previous_info:
        if "content" in changes:
            event["previous_checksum"] = previous_info["checksum"]
        if "permissions" in changes:
            event["previous_permissions"] = previous_info["permissions"]
        if "owner" in changes:
            event["previous_owner"] = previous_info["owner"]
        if "size" in changes:
            event["previous_size"] = previous_info["size"]

    return event


def create_deletion_event(
    hostname: str,
    file_path: str,
    previous_info: dict[str, Any],
) -> dict[str, Any]:
    """Create a standardized event dictionary for file deletion events.

    Includes the previous state of the file before deletion.

    Args:
        hostname: Hostname or IP of the AIX system where deletion occurred
        file_path: Absolute path to the deleted file
        previous_info: Previous file information before deletion

    Note:
        Always sets action="deleted", changed=True, and changes=["deleted"].

    Returns:
        dict: Event with deletion details and previous file metadata
    """
    return {
        "timestamp": get_current_timestamp(),
        "host": hostname,
        "file": file_path,
        "action": "deleted",
        "changed": True,
        "changes": ["deleted"],
        "previous_checksum": previous_info["checksum"],
        "previous_permissions": previous_info["permissions"],
        "previous_owner": previous_info["owner"],
        "previous_size": previous_info["size"],
        "source": "aix_file_watch",
    }


def create_error_event(hostname: str, error_message: str) -> dict[str, Any]:
    """Create a standardized event dictionary for error conditions.

    Allows EDA rules to detect and respond to monitoring failures.

    Args:
        hostname: Hostname or IP where the error occurred
        error_message: Description of the error that occurred

    Note:
        Always sets severity="error" for filtering in rules.

    Returns:
        dict: Event with timestamp, host, error, source, and severity
    """
    return {
        "timestamp": get_current_timestamp(),
        "host": hostname,
        "error": error_message,
        "source": "aix_file_watch",
        "severity": "error",
    }


async def scan_files_on_host(
    ssh_client: paramiko.SSHClient,
    hostname: str,
    file_list: list[str],
    file_states: dict[str, Any],
    event_queue: asyncio.Queue,
    emit_initial: bool,
) -> None:
    """Perform initial scan of all monitored files on a single AIX host.

    Establishes baseline state and optionally emits initial events.

    Args:
        ssh_client: Active SSH connection to the AIX host
        hostname: Hostname or IP of the AIX system being scanned
        file_list: List of absolute file paths to monitor
        file_states: Dictionary to store file states (modified in place)
        event_queue: Queue for emitting events to the rulebook
        emit_initial: Whether to emit events for initial file states

    Note:
        Stores None for non-existent files. Async function using await.

    Returns:
        None (modifies file_states in place, emits events to queue)
    """
    # Initialize storage for this host
    file_states[hostname] = {}

    # Check each file
    for file_path in file_list:
        file_info = get_file_info(ssh_client, file_path)

        if file_info.get("exists"):
            # Store file info
            file_states[hostname][file_path] = file_info

            # Emit initial event if requested
            if emit_initial:
                event = create_file_event(
                    hostname=hostname,
                    file_path=file_path,
                    action="initial",
                    current_info=file_info,
                    previous_info=None,
                    changes=[],
                )
                await event_queue.put(event)
        else:
            # File doesn't exist
            file_states[hostname][file_path] = None

            if emit_initial:
                event = {
                    "timestamp": get_current_timestamp(),
                    "host": hostname,
                    "file": file_path,
                    "action": "missing",
                    "changed": False,
                    "source": "aix_file_watch",
                }
                await event_queue.put(event)


async def check_file_changes(
    ssh_client: paramiko.SSHClient,
    hostname: str,
    file_path: str,
    file_states: dict[str, Any],
    event_queue: asyncio.Queue,
) -> None:
    """Check a single file for changes by comparing current state with stored state.

    Emits events for creations, modifications, and deletions.

    Args:
        ssh_client: Active SSH connection to the AIX host
        hostname: Hostname or IP of the AIX system
        file_path: Absolute path to the file being checked
        file_states: Dictionary containing stored file states
        event_queue: Queue for emitting events to the rulebook

    Note:
        Updates file_states after detecting changes. Async function using await.

    Returns:
        None (modifies file_states in place, emits events to queue)
    """
    current_info = get_file_info(ssh_client, file_path)

    # Get previous file info
    previous_info = file_states[hostname].get(file_path)

    if current_info.get("exists"):
        # File exists now

        # Detect what changed
        changes = detect_changes(current_info, previous_info)

        if changes:
            # Something changed!

            # Determine action
            action = "created" if previous_info is None else "modified"

            # Create and emit event
            event = create_file_event(
                hostname=hostname,
                file_path=file_path,
                action=action,
                current_info=current_info,
                previous_info=previous_info,
                changes=changes,
            )
            await event_queue.put(event)

            # Update stored info
            file_states[hostname][file_path] = current_info

    elif previous_info is not None:
        # File doesn't exist now and was previously tracked
        # File was deleted
        event = create_deletion_event(hostname, file_path, previous_info)
        await event_queue.put(event)

        # Update stored info
        file_states[hostname][file_path] = None


async def monitor_host(
    host_info: dict[str, Any],
    file_list: list[str],
    file_states: dict[str, Any],
    event_queue: asyncio.Queue,
) -> None:
    """Monitor all files on a single host during periodic checks.

    Creates SSH connection, checks all files, and handles errors.

    Args:
        host_info: Connection parameters for the host
        file_list: List of absolute file paths to monitor
        file_states: Dictionary containing stored file states
        event_queue: Queue for emitting events to the rulebook

    Note:
        Emits error events on connection or command failures. Async function.

    Returns:
        None (emits events to queue)
    """
    hostname = host_info["host"]

    try:
        # Connect to host
        ssh_client = create_ssh_client(host_info)

        # Check each file
        for file_path in file_list:
            await check_file_changes(ssh_client, hostname, file_path, file_states, event_queue)

        # Close connection
        ssh_client.close()

    except (OSError, paramiko.SSHException) as e:
        # Emit error event
        error_event = create_error_event(hostname, str(e))
        await event_queue.put(error_event)


async def main(queue: asyncio.Queue, args: dict[str, Any]) -> None:
    """Serve as main entry point for AIX File Watch event source plugin.

    Performs initial scan, then continuously monitors files at specified intervals.

    Args:
        queue: Event queue provided by ansible-rulebook
        args: Configuration parameters (hosts, files, interval, emit_initial)

    Note:
        Runs infinite loop with asyncio.sleep between checks. Validates required args.

    Returns:
        None (runs indefinitely, emitting events to queue)
    """
    # Get configuration
    host_list = args.get("hosts", [])
    if not host_list:
        msg = "AIXFileWatch: 'hosts' list is required."
        raise ValueError(msg)

    file_list = args.get("files", [])
    if not file_list:
        msg = "AIXFileWatch: 'files' list is required."
        raise ValueError(msg)

    check_interval = int(args.get("interval", 30))
    emit_initial = bool(args.get("emit_initial", False))

    # Storage for file states: {hostname: {file_path: file_info}}
    file_states = {}

    # Initial scan of all hosts
    for host_info in host_list:
        hostname = host_info["host"]

        try:
            # Connect to host
            ssh_client = create_ssh_client(host_info)

            # Scan all files
            await scan_files_on_host(
                ssh_client=ssh_client,
                hostname=hostname,
                file_list=file_list,
                file_states=file_states,
                event_queue=queue,
                emit_initial=emit_initial,
            )

            # Close connection
            ssh_client.close()

        except (OSError, paramiko.SSHException) as e:
            # Emit error event
            error_event = create_error_event(hostname, f"Initial connection failed: {e!s}")
            await queue.put(error_event)

    # Main monitoring loop
    while True:
        # Wait before next check
        await asyncio.sleep(check_interval)

        # Check all hosts
        for host_info in host_list:
            await monitor_host(host_info, file_list, file_states, queue)
