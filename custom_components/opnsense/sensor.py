"""Sensor entities for the OPNsense integration."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import OpnsenseFirmwareCoordinator
from .update_tracker import LastUpdateState, LastUpdateTracker


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up OPNsense sensors from a config entry."""
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
            OpnsenseFirmwareSensor(coordinator, entry, device_info),
            OpnsenseLastUpdateSensor(tracker, entry, device_info),
        ]
    )


class OpnsenseFirmwareSensor(
    CoordinatorEntity[OpnsenseFirmwareCoordinator], SensorEntity
):
    """Reports whether an OPNsense firmware update is available."""

    _attr_has_entity_name = True
    _attr_translation_key = "firmware"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["up_to_date", "update_available"]

    def __init__(
        self,
        coordinator: OpnsenseFirmwareCoordinator,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_firmware"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> str | None:
        if self.coordinator.data is None:
            return None
        return (
            "update_available"
            if self.coordinator.data.update_available
            else "up_to_date"
        )

    @property
    def extra_state_attributes(self) -> dict[str, str | bool | None]:
        data = self.coordinator.data
        if data is None:
            return {}
        return {
            "installed_version": data.installed_version,
            "candidate_version": data.candidate_version,
            "needs_reboot": data.needs_reboot,
            "status_message": data.status_message,
            "last_checked": self.coordinator.last_checked.isoformat()
            if self.coordinator.last_checked
            else None,
        }


class OpnsenseLastUpdateSensor(RestoreEntity, SensorEntity):
    """Reports the outcome of the last manually triggered OPNsense update."""

    _attr_has_entity_name = True
    _attr_translation_key = "last_update"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["idle", "in_progress", "success", "failed"]

    def __init__(
        self,
        tracker: LastUpdateTracker,
        entry: ConfigEntry,
        device_info: DeviceInfo,
    ) -> None:
        self._tracker = tracker
        self._attr_unique_id = f"{entry.entry_id}_last_update"
        self._attr_device_info = device_info
        self._remove_listener: callable | None = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state in ("success", "failed"):
            self._tracker.restore_state(
                LastUpdateState(
                    status=last_state.state,
                    triggered_at=dt_util.parse_datetime(
                        last_state.attributes.get("triggered_at") or ""
                    ),
                    completed_at=dt_util.parse_datetime(
                        last_state.attributes.get("completed_at") or ""
                    ),
                    needs_reboot=False,
                    log_tail=last_state.attributes.get("log_tail", ""),
                )
            )
        self._remove_listener = self._tracker.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener:
            self._remove_listener()
        await super().async_will_remove_from_hass()

    @property
    def native_value(self) -> str:
        return self._tracker.state.status

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        state = self._tracker.state
        return {
            "triggered_at": state.triggered_at.isoformat() if state.triggered_at else None,
            "completed_at": state.completed_at.isoformat() if state.completed_at else None,
            "log_tail": state.log_tail,
        }
