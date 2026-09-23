from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import WattrApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Wattr number entities from a config entry."""
    api: WattrApi = entry.runtime_data
    device_id = entry.data[CONF_DEVICE_ID]

    # Get the correct DataUpdateCoordinator
    coordinator: DataUpdateCoordinator = entry.coordinators.get("setpoint")
    if coordinator is None:
        _LOGGER.error("Setpoint coordinator not found for entry %s", entry.entry_id)
        return

    number = WattrSetpointNumber(coordinator, api, device_id)
    async_add_entities([number])


class WattrSetpointNumber(CoordinatorEntity, NumberEntity):
    """Representation of a water setpoint number."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, api: WattrApi, device_id: str
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)  # direct init
        self._api = api
        self._device_id = device_id

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name="Wattr Pool Controller",
            manufacturer="Sempl",
            model="Wattr",
        )

    @property
    def name(self) -> str:
        return "Water Temperature Setpoint"

    @property
    def unique_id(self) -> str:
        return f"wattr_setpoint_{self._device_id}"

    @property
    def native_min_value(self) -> float:
        return 20.0

    @property
    def native_max_value(self) -> float:
        return 35.0

    @property
    def native_step(self) -> float:
        return 0.5

    @property
    def value(self) -> float:
        return self.coordinator.data.get("setpoint", 25.0)

    async def async_set_value(self, value: float) -> None:
        """Update the setpoint via the API and refresh the coordinator."""
        try:
            await self._api.setWaterSetpoint(value)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.exception("Failed to set water setpoint: %s", err)
