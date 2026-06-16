
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Copyright (c) IBM
# SPDX-License-Identifier: Apache-2.0
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import asyncio
import csv
import hashlib
import logging
from pathlib import Path
import sys
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

DOCUMENTATION = r"""
---
name: flrt_monitor
short_description: Monitor IBM FLRT for new AIX security fixes and HIPER updates.
description:
  - Monitors IBM Fix Level Recommendation Tool (FLRT) HIPER/Security CSV for new vulnerabilities and fixes.
  - Downloads and parses IBM's public CSV file containing AIX security and HIPER fix information.
  - Detects when new vulnerabilities or fixes are published by IBM.
  - Emits events when new entries appear in the CSV, triggering automated responses.
  - Supports filtering by vulnerability type (security/HIPER), CVSS score, and product.
  - Includes retry logic, caching, and comprehensive error handling for production use.
version_added: 2.2.0
author:
  - "Nitish K Mishra (@nitismis)"
notes:
  - "Requires outbound HTTPS access to IBM's FLRT CSV endpoint."
  - "Uses aiohttp for async HTTP requests; ensure the dependency is installed."
  - "Caches CSV state locally to detect changes efficiently."
  - "Minimum poll interval is 300 seconds (5 minutes) to avoid overwhelming IBM servers."
  - "CVSS scores are extracted from the CSV and used for severity-based filtering."
requirements:
  - "python >= 3.9"
  - "ansible-rulebook"
  - "aiohttp"
options:
  csv_url:
    description:
      - URL to the IBM FLRT HIPER/Security CSV file.
      - Defaults to IBM's official public CSV endpoint.
    required: false
    type: str
    default: "https://www3.software.ibm.com/ibmdl/pub/software/server/flrtvc/hiper_security.csv"
  poll_interval:
    description:
      - Seconds between CSV checks.
      - Minimum 300 seconds (5 minutes), maximum 86400 seconds (24 hours).
    required: false
    type: int
    default: 3600
  filter_type:
    description:
      - Filter events by vulnerability type.
      - C(sec) for security vulnerabilities only.
      - C(hiper) for HIPER fixes only.
      - C(all) for both security and HIPER.
    required: false
    type: str
    choices: ['all', 'sec', 'hiper']
    default: 'all'
  filter_product:
    description:
      - Filter events by product name (case-insensitive).
      - Examples C(aix), C(vios).
      - Empty string means no product filtering.
    required: false
    type: str
    default: ''
  min_cvss_score:
    description:
      - Minimum CVSS score (0.0-10.0) to emit events.
      - Only vulnerabilities with CVSS >= this value will trigger events.
      - Use 7.0 for high/critical only, 0.0 for all severities.
    required: false
    type: float
    default: 0.0
  cache_file:
    description:
      - Local file path to cache CSV state.
      - Used to detect changes between polls.
    required: false
    type: str
    default: "/tmp/flrt_cache.csv"
  emit_on_startup:
    description:
      - If C(true), emit events for all current vulnerabilities on first run.
      - If C(false), only emit events when new vulnerabilities are detected.
    required: false
    type: bool
    default: false
  max_retries:
    description:
      - Maximum retry attempts for failed CSV downloads.
      - Uses exponential backoff between retries.
    required: false
    type: int
    default: 3
  retry_delay:
    description:
      - Initial delay in seconds between retry attempts.
      - Doubles with each retry (exponential backoff).
    required: false
    type: int
    default: 5
  request_timeout:
    description:
      - HTTP request timeout in seconds.
    required: false
    type: int
    default: 30
  log_level:
    description:
      - Logging verbosity level.
    required: false
    type: str
    choices: ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    default: 'INFO'
"""

EXAMPLES = r"""
- name: Monitor for critical AIX security vulnerabilities
  hosts: localhost
  sources:
    - ibm.power_aix.flrt_monitor:
        poll_interval: 3600
        filter_type: sec
        min_cvss_score: 9.0
        emit_on_startup: false
        log_level: INFO
  rules:
    - name: Critical vulnerability detected
      condition: event.cvss_max >= 9.0
      action:
        run_playbook:
          name: emergency_patch.yml

- name: Monitor all AIX fixes with email notifications
  hosts: localhost
  sources:
    - ibm.power_aix.flrt_monitor:
        poll_interval: 1800
        filter_type: all
        min_cvss_score: 7.0
  rules:
    - name: High severity fix available
      condition: event.cvss_max >= 7.0
      action:
        run_playbook:
          name: send_email_notification.yml

- name: Monitor OpenSSL vulnerabilities specifically
  hosts: localhost
  sources:
    - ibm.power_aix.flrt_monitor:
        poll_interval: 3600
        filter_type: sec
        min_cvss_score: 5.0
  rules:
    - name: OpenSSL vulnerability detected
      condition: event.component is search("OpenSSL", ignorecase=True)
      action:
        run_playbook:
          name: openssl_patch.yml

- name: Run FLRTVC scan on all new vulnerabilities
  hosts: localhost
  sources:
    - ibm.power_aix.flrt_monitor:
        poll_interval: 3600
        filter_type: sec
        min_cvss_score: 7.0
        emit_on_startup: true
  rules:
    - name: New vulnerability detected
      condition: event.type == "flrt_update"
      action:
        run_playbook:
          name: run_flrtvc.yml
"""

RETURN = r"""
type:
  description: Event type identifier.
  type: str
  returned: always
  sample: "flrt_update"
vulnerability_type:
  description: Type of vulnerability (sec for security, hiper for HIPER).
  type: str
  returned: always
  sample: "sec"
product:
  description: Affected product name.
  type: str
  returned: always
  sample: "aix"
component:
  description: Affected component or software package.
  type: str
  returned: always
  sample: "OpenSSL"
abstract:
  description: Brief description of the vulnerability or fix.
  type: str
  returned: always
  sample: "AIX is vulnerable to arbitrary code execution due to OpenSSL"
apars:
  description: List of APAR numbers and CVE IDs associated with this fix.
  type: list
  elements: str
  returned: always
  sample: ["CVE-2024-4741", "CVE-2024-5535", "1122401sa"]
fixed_in:
  description: Version or fix level where issue is resolved.
  type: str
  returned: always
  sample: "See Bulletin"
ifixes:
  description: List of interim fix (ifix) filenames available.
  type: list
  elements: str
  returned: always
  sample: ["1122400a.240722.epkg.Z", "3013sa.240722.epkg.Z"]
bulletin_url:
  description: URL to IBM security bulletin with detailed information.
  type: str
  returned: always
  sample: "https://aix.software.ibm.com/aix/efixes/security/openssl_advisory42.asc"
filesets:
  description: List of affected AIX filesets with version ranges.
  type: list
  elements: str
  returned: always
  sample: ["openssl.base:1.1.1.0-1.1.1.2400", "openssl.base:3.0.0.0-3.0.13.1000"]
issued_date:
  description: Date when the fix was first issued (YYYYMMDD format).
  type: str
  returned: always
  sample: "20240730"
updated_date:
  description: Date when the fix information was last updated.
  type: str
  returned: always
  sample: "20240801"
download_url:
  description: URL to download the fix package.
  type: str
  returned: always
  sample: "https://aix.software.ibm.com/aix/efixes/security/openssl_fix42.tar"
cvss_max:
  description: Maximum CVSS score among all CVEs in this vulnerability.
  type: float
  returned: always
  sample: 8.1
cves:
  description: List of CVE details with individual scores.
  type: list
  elements: dict
  returned: always
  sample: [{"id": "CVE-2024-4741", "score": 8.1}, {"id": "CVE-2024-5535", "score": 3.7}]
reboot_required:
  description: Whether system reboot is required after applying fix.
  type: str
  returned: always
  sample: "no"
timestamp:
  description: UTC timestamp when event was generated (ISO 8601 format).
  type: str
  returned: always
  sample: "2026-06-15T05:26:25.347548+00:00"
source:
  description: Source identifier for the event.
  type: str
  returned: always
  sample: "flrt_monitor"
error:
  description: Error message if monitoring failed.
  type: str
  returned: on error
  sample: "Failed to download CSV after 3 attempts"
consecutive_errors:
  description: Number of consecutive errors encountered.
  type: int
  returned: on error
  sample: 2
"""


# Default IBM FLRT HIPER/Security CSV URL
DEFAULT_CSV_URL = "https://www3.software.ibm.com/ibmdl/pub/software/server/flrtvc/hiper_security.csv"

# Constants
MIN_POLL_INTERVAL = 300  # 5 minutes minimum to avoid overwhelming IBM servers
MAX_POLL_INTERVAL = 86400  # 24 hours maximum
DEFAULT_POLL_INTERVAL = 3600  # 1 hour
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5
DEFAULT_REQUEST_TIMEOUT = 30
MAX_CACHE_SIZE_MB = 100  # Maximum cache file size


# Configure logging
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging with specified level.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance

    """
    logger = logging.getLogger("flrt_monitor")

    # Remove existing handlers
    logger.handlers = []

    # Set level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


async def main(
    queue: asyncio.Queue,
    args: dict[str, Any],
) -> None:
    """Serve as main entry point for the EDA event source plugin.

    Args:
        queue: Async queue to send events to the rule engine
        args: Configuration arguments from the rulebook

    """
    # Setup logging
    log_level = args.get("log_level", "INFO")
    logger = setup_logging(log_level)

    logger.info("IBM FLRT Monitor starting...")

    # Extract and validate configuration
    try:
        config = validate_configuration(args, logger)
    except ValueError as e:
        error_event = {
            "type": "error",
            "error": f"Configuration error: {e!s}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await queue.put(error_event)
        logger.exception("Configuration error")
        return

    csv_url = config["csv_url"]
    poll_interval = config["poll_interval"]
    filter_type = config["filter_type"]
    filter_product = config["filter_product"]
    min_cvss_score = config["min_cvss_score"]
    cache_file = config["cache_file"]
    emit_on_startup = config["emit_on_startup"]
    max_retries = config["max_retries"]
    retry_delay = config["retry_delay"]
    request_timeout = config["request_timeout"]

    logger.info(
        "Configuration: poll_interval=%ss, filter_type=%s, min_cvss_score=%s, max_retries=%s",
        poll_interval, filter_type, min_cvss_score, max_retries,
    )

    monitor = FLRTMonitor(
        csv_url=csv_url,
        cache_file=cache_file,
        filter_type=filter_type,
        filter_product=filter_product,
        min_cvss_score=min_cvss_score,
        max_retries=max_retries,
        retry_delay=retry_delay,
        request_timeout=request_timeout,
        logger=logger,
    )

    # Initial check
    try:
        await monitor.initialize()
        logger.info("Monitor initialized successfully")
    except (OSError, ValueError, RuntimeError):
        logger.exception("Initialization failed")
        error_event = {
            "type": "error",
            "error": f"Initialization failed: {e!s}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        await queue.put(error_event)

    if emit_on_startup:
        logger.info("Emitting current vulnerabilities on startup...")
        try:
            initial_events = await monitor.get_all_vulnerabilities()
            logger.info("Found %s current vulnerabilities", len(initial_events))
            for event in initial_events:
                await queue.put(event)
        except (OSError, ValueError, RuntimeError):
            logger.exception("Failed to get initial vulnerabilities")

    # Continuous monitoring loop
    consecutive_errors = 0
    max_consecutive_errors = 5

    while True:
        try:
            logger.debug("Checking for updates from %s", csv_url)
            new_events = await monitor.check_for_updates()

            if new_events:
                logger.info("Found %s new vulnerabilities", len(new_events))
                for event in new_events:
                    await queue.put(event)
                    logger.debug("Emitted event for %s", event.get("component", "unknown"))
            else:
                logger.debug("No new vulnerabilities found")

            # Reset error counter on success
            consecutive_errors = 0

            await asyncio.sleep(poll_interval)

        except (OSError, ValueError, RuntimeError):
            consecutive_errors += 1
            logger.exception(
                "Error in monitoring loop (attempt %s/%s): %s",
                consecutive_errors, max_consecutive_errors, e,
            )

            error_event = {
                "type": "error",
                "error": str(e),
                "consecutive_errors": consecutive_errors,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            await queue.put(error_event)

            if consecutive_errors >= max_consecutive_errors:
                logger.critical("Too many consecutive errors (%s). Stopping monitor.", consecutive_errors)
                break

            # Exponential backoff
            backoff_delay = min(60 * (2 ** consecutive_errors), 300)  # Max 5 minutes
            logger.info("Waiting %ss before retry...", backoff_delay)
            await asyncio.sleep(backoff_delay)


def validate_configuration(args: dict[str, Any], logger: logging.Logger) -> dict[str, Any]:
    """Validate and normalize configuration parameters.

    Args:
        args: Raw configuration from rulebook
        logger: Logger instance

    Returns:
        Validated configuration dictionary

    Raises:
        ValueError: If configuration is invalid

    """
    config = {}

    # CSV URL
    csv_url = args.get("csv_url", DEFAULT_CSV_URL)
    parsed_url = urlparse(csv_url)
    if parsed_url.scheme not in ["http", "https", "file"]:
        msg = f"Invalid CSV URL scheme: {parsed_url.scheme}"
        raise ValueError(msg)
    config["csv_url"] = csv_url

    # Poll interval
    poll_interval = int(args.get("poll_interval", DEFAULT_POLL_INTERVAL))
    if poll_interval < MIN_POLL_INTERVAL:
        logger.warning(
            "poll_interval %ss is below minimum %ss. Using minimum.",
            poll_interval, MIN_POLL_INTERVAL,
        )
        poll_interval = MIN_POLL_INTERVAL
    if poll_interval > MAX_POLL_INTERVAL:
        logger.warning(
            "poll_interval %ss exceeds maximum %ss. Using maximum.",
            poll_interval, MAX_POLL_INTERVAL,
        )
        poll_interval = MAX_POLL_INTERVAL
    config["poll_interval"] = poll_interval

    # Filter type
    filter_type = args.get("filter_type", "all").lower()
    if filter_type not in ["all", "sec", "hiper"]:
        msg = f"Invalid filter_type: {filter_type}. Must be 'all', 'sec', or 'hiper'"
        raise ValueError(msg)
    config["filter_type"] = filter_type

    # Filter product
    config["filter_product"] = args.get("filter_product", "").lower()

    # CVSS score
    max_cvss_score = 10.0
    min_cvss_score = float(args.get("min_cvss_score", 0.0))
    if not (0.0 <= min_cvss_score <= max_cvss_score):
        msg = f"min_cvss_score must be between 0.0 and 10.0, got {min_cvss_score}"
        raise ValueError(msg)
    config["min_cvss_score"] = min_cvss_score

    # Cache file
    cache_file = args.get("cache_file", "/tmp/flrt_cache.csv")  # Default temp location
    cache_path = Path(cache_file)
    cache_dir = str(cache_path.parent)
    if cache_dir and cache_dir != "." and not cache_path.parent.exists():
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info("Created cache directory: %s", cache_dir)
        except OSError as e:
            msg = f"Cannot create cache directory {cache_dir}: {e}"
            raise ValueError(msg) from e
    config["cache_file"] = cache_file

    # Emit on startup
    config["emit_on_startup"] = bool(args.get("emit_on_startup", False))

    # Retry configuration
    config["max_retries"] = int(args.get("max_retries", DEFAULT_MAX_RETRIES))
    config["retry_delay"] = int(args.get("retry_delay", DEFAULT_RETRY_DELAY))
    config["request_timeout"] = int(args.get("request_timeout", DEFAULT_REQUEST_TIMEOUT))

    return config


class FLRTMonitor:
    """Monitor IBM FLRT CSV for changes and new vulnerabilities."""

    def __init__(
        self,
        csv_url: str,
        cache_file: str,
        filter_type: str = "all",
        filter_product: str = "",
        min_cvss_score: float = 0.0,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: int = DEFAULT_RETRY_DELAY,
        request_timeout: int = DEFAULT_REQUEST_TIMEOUT,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize FLRT Monitor.

        Args:
            csv_url: URL to FLRT CSV file
            cache_file: Path to cache file
            filter_type: Filter type (all, sec, hiper)
            filter_product: Product filter string
            min_cvss_score: Minimum CVSS score threshold
            max_retries: Maximum retry attempts
            retry_delay: Delay between retries in seconds
            request_timeout: Request timeout in seconds
            logger: Logger instance

        """
        self.csv_url = csv_url
        self.cache_file = cache_file
        self.filter_type = filter_type
        self.filter_product = filter_product
        self.min_cvss_score = min_cvss_score
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.request_timeout = request_timeout
        self.logger = logger or logging.getLogger("flrt_monitor")
        self.previous_hash = None
        self.previous_entries = set()

    async def initialize(self) -> None:
        """Initialize the monitor by loading cached state if available."""
        cache_path = Path(self.cache_file)
        if cache_path.exists():
            try:
                # Check cache file size
                cache_size_mb = cache_path.stat().st_size / (1024 * 1024)
                if cache_size_mb > MAX_CACHE_SIZE_MB:
                    self.logger.warning("Cache file size (%.2fMB) exceeds maximum (%sMB). Removing old cache.", cache_size_mb, MAX_CACHE_SIZE_MB)
                    cache_path.unlink()
                    return

                with cache_path.open() as f:
                    cached_data = f.read()
                    self.previous_hash = hashlib.md5(cached_data.encode()).hexdigest()

                    # Parse cached entries
                    reader = csv.DictReader(cached_data.splitlines())
                    for row in reader:
                        if self._should_process_row(row):
                            entry_id = self._generate_entry_id(row)
                            self.previous_entries.add(entry_id)

                self.logger.info("Loaded %s entries from cache", len(self.previous_entries))
            except (OSError, ValueError) as e:
                self.logger.warning("Could not load cache file: %s", e)

    async def _download_csv_with_retry(self) -> str:
        """Download CSV with retry logic and exponential backoff.

        Returns:
            CSV content as string

        Raises:
            Exception: If all retry attempts fail

        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                self.logger.debug("Download attempt %s/%s", attempt + 1, self.max_retries)

                timeout = aiohttp.ClientTimeout(total=self.request_timeout)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(self.csv_url) as response:
                        if response.status != 200:
                            msg = f"HTTP {response.status}: {response.reason}"
                            raise Exception(msg)

                        csv_content = await response.text()
                        self.logger.debug("Downloaded %s bytes", len(csv_content))
                        return csv_content

            except asyncio.TimeoutError as e:
                last_exception = e
                self.logger.warning("Request timeout on attempt %s", attempt + 1)
            except aiohttp.ClientError as e:
                last_exception = e
                self.logger.warning("Network error on attempt %s: %s", attempt + 1, e)
            except (OSError, ValueError) as e:
                last_exception = e
                self.logger.warning("Error on attempt %s: %s", attempt + 1, e)

            if attempt < self.max_retries - 1:
                # Exponential backoff
                delay = self.retry_delay * (2 ** attempt)
                self.logger.info("Retrying in %ss...", delay)
                await asyncio.sleep(delay)

        msg = f"Failed to download CSV after {self.max_retries} attempts: {last_exception}"
        raise Exception(msg)

    async def check_for_updates(self) -> list[dict[str, Any]]:
        """Check for updates in the FLRT CSV and return new vulnerability events.

        Returns:
            List of event dictionaries for new vulnerabilities

        """
        events = []

        try:
            # Download current CSV with retry
            csv_content = await self._download_csv_with_retry()

            # Calculate hash
            current_hash = hashlib.md5(csv_content.encode()).hexdigest()

            # Check if CSV has changed
            if current_hash == self.previous_hash:
                self.logger.debug("CSV unchanged")
                return events

            self.logger.info("CSV has changed, processing updates...")

            # Parse CSV and find new entries
            current_entries = set()
            reader = csv.DictReader(csv_content.splitlines())

            for row in reader:
                if not self._should_process_row(row):
                    continue

                entry_id = self._generate_entry_id(row)
                current_entries.add(entry_id)

                # Check if this is a new entry
                if entry_id not in self.previous_entries:
                    event = self._create_event(row)
                    events.append(event)
                    self.logger.info("New vulnerability: %s (CVSS: %s)", event["component"], event["cvss_max"])

            # Update cache
            try:
                cache_path = Path(self.cache_file)
                with cache_path.open("w") as f:
                    f.write(csv_content)
                self.logger.debug("Updated cache file: %s", self.cache_file)
            except (OSError, ValueError) as e:
                self.logger.exception("Failed to update cache")

            self.previous_hash = current_hash
            self.previous_entries = current_entries

        except (OSError, ValueError) as e:
            self.logger.exception("Error checking for updates")
            raise

        return events

    async def get_all_vulnerabilities(self) -> list[dict[str, Any]]:
        """Get all current vulnerabilities from the CSV.

        Returns:
            List of event dictionaries for all vulnerabilities

        """
        events = []

        try:
            csv_content = await self._download_csv_with_retry()

            reader = csv.DictReader(csv_content.splitlines())

            for row in reader:
                if self._should_process_row(row):
                    event = self._create_event(row)
                    events.append(event)

        except (OSError, ValueError) as e:
            self.logger.exception("Error getting vulnerabilities")
            raise

        return events

    def _should_process_row(self, row: dict[str, str]) -> bool:
        """Determine if a CSV row should be processed based on filters."""
        # Skip header/metadata rows
        if not row.get("type") or row["type"] in ["type", "0.8.14"]:
            return False

        # Filter by type (sec/hiper)
        if self.filter_type != "all" and row.get("type") != self.filter_type:
            return False

        # Filter by product
        if self.filter_product and self.filter_product not in row.get("product", "").lower():
            return False

        # Filter by CVSS score
        cvss_max = self._extract_max_cvss(row.get("cvss", ""))
        return not cvss_max < self.min_cvss_score

    def _generate_entry_id(self, row: dict[str, str]) -> str:
        """Generate a unique ID for a CSV entry."""
        key_parts = [
            row.get("type", ""),
            row.get("product", ""),
            row.get("versions", ""),
            row.get("apars", ""),
        ]
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()

    def _extract_max_cvss(self, cvss_string: str) -> float:
        """Extract maximum CVSS score from the cvss field."""
        if not cvss_string:
            return 0.0

        try:
            scores = []
            for part_str in cvss_string.split("/"):
                if ":" in part_str:
                    score_str = part_str.split(":")[1].strip()
                    scores.append(float(score_str))

            return max(scores) if scores else 0.0
        except (OSError, ValueError) as e:
            self.logger.debug("Could not parse CVSS string '%s': %s", cvss_string, e)
            return 0.0

    def _parse_cves(self, cvss_string: str) -> list[dict[str, Any]]:
        """Parse CVE information from cvss field."""
        cves = []
        if not cvss_string:
            return cves

        try:
            for part_str in cvss_string.split("/"):
                part = part_str.strip()
                if ":" in part:
                    cve_id, score = part.split(":")
                    cves.append({
                        "id": cve_id.strip(),
                        "score": float(score.strip()),
                    })
        except (OSError, ValueError) as e:
            self.logger.debug("Could not parse CVEs from '%s': %s", cvss_string, e)

        return cves

    def _create_event(self, row: dict[str, str]) -> dict[str, Any]:
        """Create an event dictionary from a CSV row."""
        cvss_max = self._extract_max_cvss(row.get("cvss", ""))
        cves = self._parse_cves(row.get("cvss", ""))

        return {
            "type": "flrt_update",
            "vulnerability_type": row.get("type", ""),
            "product": row.get("product", ""),
            "component": row.get("versions", ""),
            "abstract": row.get("abstract", ""),
            "apars": row.get("apars", "").split(" / ") if row.get("apars") else [],
            "fixed_in": row.get("fixedIn", ""),
            "ifixes": row.get("ifixes", "").split() if row.get("ifixes") else [],
            "bulletin_url": row.get("bulletinUrl", ""),
            "filesets": row.get("filesets", "").split() if row.get("filesets") else [],
            "issued_date": row.get("issued", ""),
            "updated_date": row.get("updated", ""),
            "download_url": row.get("download", ""),
            "cvss_max": cvss_max,
            "cves": cves,
            "reboot_required": row.get("reboot", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "flrt_monitor",
        }


if __name__ == "__main__":
    """Allow testing the plugin standalone."""

    class MockQueue:
        """Mock queue for testing."""

        """Put an item in the mock queue."""
        async def put(self, item: dict[str, Any]) -> None:
            pass

    """Test function for FLRT monitor."""
    async def test() -> None:
        queue = MockQueue()
        args = {
            "poll_interval": 10,
            "filter_type": "sec",
            "min_cvss_score": 7.0,
            "emit_on_startup": True,
            "log_level": "INFO",
        }

        await main(queue, args)

    asyncio.run(test())
