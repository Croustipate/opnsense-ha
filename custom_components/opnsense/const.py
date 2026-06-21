"""Constants for the OPNsense integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "opnsense"

CONF_VERIFY_SSL = "verify_ssl"
DEFAULT_VERIFY_SSL = False

SCAN_INTERVAL = timedelta(hours=1)
