from __future__ import annotations

import logging
from datetime import datetime, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_DEVICE_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import SCAN_INTERVAL, WattrConfigEntry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WattrConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Wattr sensors from a config entry."""
    api = entry.runtime_data
    device_id = entry.data[CONF_DEVICE_ID]

    async def async_update_data():
        """Fetch all water quality and temperature data from API."""
        try:
            quality = await api.get_waterQuality()
            temp = await api.get_waterTemperature()

            return {
                "ph": quality["data"].get("PH"),
                "rx": quality["data"].get("RX"),
                "temperature": temp.get("lastTemp"),
                "temp_age": temp.get("secondsAgo"),
            }
        except Exception as err:
            _LOGGER.error("Error fetching data from Wattr API: %s", err)
            raise

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="wattr_sensors",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,  # 5 minuten, consistent met andere coordinators
    )

    # Eerste update forceren
    await coordinator.async_config_entry_first_refresh()

    entities = [
        WattrPhSensor(coordinator, entry.entry_id, device_id),
        WattrRxSensor(coordinator, entry.entry_id, device_id),
        WattrTemperatureSensor(coordinator, entry.entry_id, device_id),
    ]

    async_add_entities(entities)

    # Notification sensor
    notifications_coordinator: DataUpdateCoordinator = entry.coordinators.get("notifications")
    if notifications_coordinator is not None:
        async_add_entities([WattrNotificationSensor(notifications_coordinator, entry.entry_id, device_id)])


class WattrBaseSensor(CoordinatorEntity, SensorEntity):
    """Basisentity voor Wattr-sensoren."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DataUpdateCoordinator, entry_id: str, device_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._device_id = device_id

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name="Wattr Pool Controller",
            manufacturer="Sempl",
            model="Wattr",
        )


class WattrPhSensor(WattrBaseSensor):
    """Sensor voor pH-waarde."""

    _attr_name = "Water pH"
    _attr_device_class = SensorDeviceClass.PH
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry_id}_ph"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("ph")


class WattrRxSensor(WattrBaseSensor):
    """Sensor voor redox (RX) waarde."""

    _attr_name = "Water Redox"
    _attr_device_class = SensorDeviceClass.VOLTAGE  # RX meestal in mV
    _attr_native_unit_of_measurement = "mV"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry_id}_rx"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("rx")


class WattrTemperatureSensor(WattrBaseSensor):
    """Sensor voor watertemperatuur."""

    _attr_name = "Watertemperatuur"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "°C"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self) -> str:
        return f"{self._entry_id}_temperature"

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get("temperature")

    @property
    def extra_state_attributes(self) -> dict:
        """Voeg extra info toe zoals age van de meting."""
        return {
            "seconds_ago": self.coordinator.data.get("temp_age"),
        }


class WattrNotificationSensor(WattrBaseSensor):
    """Sensor showing the count of active Wattr notifications."""

    _attr_name = "Wattr Notifications"
    _attr_icon = "mdi:bell"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "notifications"

    @property
    def unique_id(self) -> str:
        return f"{self._entry_id}_notifications"

    def _active_notifications(self) -> list[dict]:
        notifications = (self.coordinator.data or {}).get("notifications", [])
        return [n for n in notifications if n.get("notification", {}).get("active", False)]

    @property
    def native_value(self) -> int:
        return len(self._active_notifications())

    @property
    def extra_state_attributes(self) -> dict:
        result = []
        for n in self._active_notifications():
            notif = n.get("notification", {})
            ntype = notif.get("type", {})
            ts_ms = notif.get("timestamp")
            timestamp = (
                datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat()
                if ts_ms
                else None
            )
            result.append({
                "topic": ntype.get("topic"),
                "title": notif.get("title", {}).get("en"),
                "timestamp": timestamp,
            })
        return {"active_notifications": result}
