"""The OPNsense integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OpnsenseClient
from .config_flow import CONF_API_SECRET
from .const import CONF_VERIFY_SSL, DOMAIN
from .coordinator import OpnsenseFirmwareCoordinator
from .update_tracker import LastUpdateTracker

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OPNsense from a config entry."""
    session = async_get_clientsession(hass, verify_ssl=entry.data[CONF_VERIFY_SSL])
    client = OpnsenseClient(
        session,
        entry.data[CONF_HOST],
        entry.data[CONF_API_KEY],
        entry.data[CONF_API_SECRET],
    )
    coordinator = OpnsenseFirmwareCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    tracker = LastUpdateTracker(client, coordinator)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "tracker": tracker,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an OPNsense config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
