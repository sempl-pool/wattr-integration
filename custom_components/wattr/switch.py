"""Switch platform for Wattr integration."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import WattrApi

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Wattr switches from a config entry."""
    api: WattrApi = entry.runtime_data
    device_id = entry.data[CONF_DEVICE_ID]

    # Fetch the coordinator for smart mode
    coordinator: DataUpdateCoordinator = entry.coordinators.get("smart_mode")
    if coordinator is None:
        _LOGGER.error("Smart mode coordinator not found for entry %s", entry.entry_id)
        return

    switch = WattrSmartModeSwitch(coordinator, api, device_id)
    async_add_entities([switch])


class WattrSmartModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Wattr Smart Mode switch."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, api: WattrApi, device_id: str
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        self._api = api
        self._device_id = device_id

    @property
    def name(self) -> str:
        return "Wattr Smart Mode"

    @property
    def unique_id(self) -> str:
        return f"wattr_smart_mode_{self._device_id}"

    @property
    def is_on(self) -> bool:
        # Coordinator must store the current state in data
        return bool(self.coordinator.data.get("smart_mode", False))

    async def async_turn_on(self, **kwargs) -> None:
        """Turn smart mode on."""
        try:
            await self._api.setSmartMode(True)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.exception("Failed to turn on smart mode: %s", err)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn smart mode off."""
        try:
            await self._api.setSmartMode(False)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.exception("Failed to turn off smart mode: %s", err)
