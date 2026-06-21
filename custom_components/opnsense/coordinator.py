"""DataUpdateCoordinator for the OPNsense integration."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .api import FirmwareStatus, OpnsenseApiError, OpnsenseClient
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class OpnsenseFirmwareCoordinator(DataUpdateCoordinator[FirmwareStatus]):
    """Polls OPNsense hourly for firmware update availability."""

    def __init__(self, hass: HomeAssistant, client: OpnsenseClient) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self._client = client
        self.last_checked: datetime | None = None

    async def _async_update_data(self) -> FirmwareStatus:
        try:
            await self._client.async_check_firmware()
            status = await self._client.async_get_status()
        except OpnsenseApiError as err:
            raise UpdateFailed(f"Error communicating with OPNsense: {err}") from err
        self.last_checked = dt_util.utcnow()
        return status
