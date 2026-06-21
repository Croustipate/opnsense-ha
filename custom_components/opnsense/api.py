"""API client for the OPNsense firmware REST API."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class OpnsenseApiError(Exception):
    """Base error for the OPNsense API client."""


class OpnsenseAuthError(OpnsenseApiError):
    """Raised when authentication with the OPNsense API fails."""


class OpnsenseConnectionError(OpnsenseApiError):
    """Raised when the OPNsense API cannot be reached."""


@dataclass
class FirmwareStatus:
    """Parsed result of a firmware status check."""

    installed_version: str
    candidate_version: str | None
    update_available: bool
    needs_reboot: bool
    status_message: str


class OpnsenseClient:
    """Thin async wrapper around the OPNsense firmware REST API."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        api_key: str,
        api_secret: str,
    ) -> None:
        self._session = session
        self._base_url = host.rstrip("/")
        self._auth = aiohttp.BasicAuth(api_key, api_secret)

    async def _request(self, method: str, path: str) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            async with self._session.request(
                method,
                url,
                auth=self._auth,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status in (401, 403):
                    raise OpnsenseAuthError(
                        f"Authentication failed calling {path} (HTTP {response.status})"
                    )
                response.raise_for_status()
                return await response.json()
        except OpnsenseAuthError:
            raise
        except aiohttp.ClientError as err:
            raise OpnsenseConnectionError(f"Error calling {path}: {err}") from err

    async def async_check_firmware(self) -> None:
        """Trigger a fresh firmware check against the OPNsense repositories."""
        await self._request("POST", "/api/core/firmware/check")

    async def async_get_status(self) -> FirmwareStatus:
        """Return the current firmware status."""
        data = await self._request("GET", "/api/core/firmware/status")
        installed_version = data.get("product_version", "unknown")
        candidate_version = data.get("product", {}).get("product_latest")
        update_available = data.get("status", "none") != "none"
        needs_reboot = data.get("needs_reboot") == "1"
        status_message = data.get("status_msg", "")
        return FirmwareStatus(
            installed_version=installed_version,
            candidate_version=candidate_version,
            update_available=update_available,
            needs_reboot=needs_reboot,
            status_message=status_message,
        )

    async def async_start_upgrade(self) -> None:
        """Trigger the firmware upgrade process on OPNsense."""
        await self._request("POST", "/api/core/firmware/upgrade")

    async def async_get_upgrade_status(self) -> dict[str, Any]:
        """Return the raw upgrade/check job payload (status + log)."""
        return await self._request("GET", "/api/core/firmware/upgradestatus")
