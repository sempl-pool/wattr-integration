"""Switch platform for Wattr integration."""

from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
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

RELAY_FUNCTION_TOGGLE = 4
RELAY_FUNCTION_PULSE = 5


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

    # Set up relay switches
    relay_coordinator: DataUpdateCoordinator = entry.coordinators.get("relays")
    if relay_coordinator is None:
        _LOGGER.error("Relay coordinator not found for entry %s", entry.entry_id)
        return

    known_relay_ids: set = set()

    def _add_new_relay_entities() -> None:
        data = relay_coordinator.data or {}
        relays = data.get("relays", [])
        new_entities = []
        for relay in relays:
            relay_id = relay.get("id")
            if relay_id is not None and relay_id not in known_relay_ids:
                known_relay_ids.add(relay_id)
                new_entities.append(
                    WattrRelaySwitch(relay_coordinator, api, device_id, relay)
                )
        if new_entities:
            async_add_entities(new_entities)

    _add_new_relay_entities()
    relay_coordinator.async_add_listener(_add_new_relay_entities)


class WattrSmartModeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the Wattr Smart Mode switch."""

    def __init__(
        self, coordinator: DataUpdateCoordinator, api: WattrApi, device_id: str
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
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


class WattrRelaySwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Wattr toggle or pulse relay as a switch."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api: WattrApi,
        device_id: str,
        relay_info: dict,
    ) -> None:
        CoordinatorEntity.__init__(self, coordinator)
        self._api = api
        self._device_id = device_id
        self._relay_id = relay_info["id"]  # keep original type (int) for API calls
        self._relay_name = relay_info.get("name", str(self._relay_id))
        self._relay_function = relay_info.get("function")

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
        return f"Wattr Relay {self._relay_name}"

    @property
    def unique_id(self) -> str:
        return f"wattr_relay_{self._device_id}_{self._relay_id}"

    @property
    def icon(self) -> str:
        if self._relay_function == RELAY_FUNCTION_PULSE:
            return "mdi:electric-switch"
        return "mdi:toggle-switch"

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        for relay in data.get("relays", []):
            if relay.get("id") == self._relay_id:
                return bool(relay.get("state", False))
        return False

    async def async_turn_on(self, **kwargs) -> None:
        """Activate the relay."""
        try:
            await self._api.activate_relay(self._relay_id, True)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.exception("Failed to activate relay %s: %s", self._relay_id, err)

    async def async_turn_off(self, **kwargs) -> None:
        """Deactivate the relay."""
        try:
            await self._api.activate_relay(self._relay_id, False)
            await self.coordinator.async_request_refresh()
        except Exception as err:
            _LOGGER.exception("Failed to deactivate relay %s: %s", self._relay_id, err)
