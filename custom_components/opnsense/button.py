"""Button entities for the OPNsense integration."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import OpnsenseApiError
from .const import DOMAIN
from .coordinator import OpnsenseFirmwareCoordinator
from .update_tracker import LastUpdateTracker


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up OPNsense buttons from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: OpnsenseFirmwareCoordinator = data["coordinator"]
    tracker: LastUpdateTracker = data["tracker"]
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="OPNsense",
        manufacturer="Deciso",
        configuration_url=entry.data[CONF_HOST],
    )
    async_add_entities(
        [
            OpnsenseCheckNowButton(coordinator, entry, device_info),
            OpnsenseInstallUpdateButton(coordinator, tracker, entry, device_info),
        ]
    )


class OpnsenseCheckNowButton(ButtonEntity):
    """Button that forces an immediate firmware check."""

    _attr_has_entity_name = True
    _attr_translation_key = "check_now"

    def __init__(
        self,
        coordinator: OpnsenseFirmwareCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_check_now"
        self._attr_device_info = device_info

    async def async_press(self) -> None:
        """Force a refresh of the firmware coordinator."""
        await self._coordinator.async_request_refresh()


class OpnsenseInstallUpdateButton(ButtonEntity):
    """Button that triggers the firmware upgrade on OPNsense."""

    _attr_has_entity_name = True
    _attr_translation_key = "install_update"

    def __init__(
        self,
        coordinator: OpnsenseFirmwareCoordinator,
        tracker: LastUpdateTracker,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        self._coordinator = coordinator
        self._tracker = tracker
        self._attr_unique_id = f"{entry.entry_id}_install_update"
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        """Only allow triggering an upgrade when one is actually pending."""
        return bool(self._coordinator.data and self._coordinator.data.update_available)

    async def async_press(self) -> None:
        """Trigger the firmware upgrade."""
        try:
            await self._tracker.async_start_upgrade()
        except OpnsenseApiError as err:
            raise HomeAssistantError(f"Failed to start OPNsense upgrade: {err}") from err
