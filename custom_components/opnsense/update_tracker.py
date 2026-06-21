"""Tracks a manually triggered OPNsense firmware upgrade to completion."""
from __future__ import annotations

import asyncio
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.util import dt as dt_util

from .api import OpnsenseApiError, OpnsenseClient
from .coordinator import OpnsenseFirmwareCoordinator

_LOGGER = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 20
MAX_WAIT_SECONDS = 15 * 60

_FAILURE_PATTERNS = re.compile(r"error|failed|aborting", re.IGNORECASE)


@dataclass
class LastUpdateState:
    """Snapshot of the last manually triggered update."""

    status: str = "idle"  # idle | in_progress | success | failed
    triggered_at: datetime | None = None
    completed_at: datetime | None = None
    needs_reboot: bool = False
    log_tail: str = ""


class LastUpdateTracker:
    """Triggers an OPNsense upgrade and tracks its outcome in the background."""

    def __init__(
        self, client: OpnsenseClient, coordinator: OpnsenseFirmwareCoordinator
    ) -> None:
        self._client = client
        self._coordinator = coordinator
        self.state = LastUpdateState()
        self._listeners: list[Callable[[], None]] = []

    def async_add_listener(self, callback: Callable[[], None]) -> Callable[[], None]:
        """Register a callback invoked whenever the state changes."""
        self._listeners.append(callback)

        def remove() -> None:
            self._listeners.remove(callback)

        return remove

    def restore_state(self, state: LastUpdateState) -> None:
        """Restore a previously persisted terminal state (used by RestoreEntity)."""
        if self.state.status == "idle":
            self.state = state

    def _notify(self) -> None:
        for callback in list(self._listeners):
            callback()

    async def async_start_upgrade(self) -> None:
        """Trigger the firmware upgrade and track it to completion in the background."""
        self.state = LastUpdateState(status="in_progress", triggered_at=dt_util.utcnow())
        self._notify()
        await self._client.async_start_upgrade()
        asyncio.create_task(self._async_track_upgrade())

    async def _async_track_upgrade(self) -> None:
        elapsed = 0
        while elapsed < MAX_WAIT_SECONDS:
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
            elapsed += POLL_INTERVAL_SECONDS
            try:
                payload = await self._client.async_get_upgrade_status()
            except OpnsenseApiError:
                _LOGGER.debug("Firewall unreachable while tracking upgrade, retrying")
                continue

            if payload.get("status") != "done":
                continue

            log = payload.get("log", "")
            success = "***DONE***" in log and not _FAILURE_PATTERNS.search(log)
            await self._coordinator.async_request_refresh()
            needs_reboot = bool(
                self._coordinator.data and self._coordinator.data.needs_reboot
            )
            self.state = LastUpdateState(
                status="success" if success else "failed",
                triggered_at=self.state.triggered_at,
                completed_at=dt_util.utcnow(),
                needs_reboot=needs_reboot,
                log_tail=log[-2000:],
            )
            self._notify()
            return

        self.state = LastUpdateState(
            status="failed",
            triggered_at=self.state.triggered_at,
            completed_at=dt_util.utcnow(),
            log_tail="Firewall unreachable after 15 minutes, giving up.",
        )
        self._notify()
