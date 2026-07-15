"""The wattr integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WattrApi
from .const import CONF_LINKED_SENSOR

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
_PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER, Platform.SWITCH]

# TODO Create ConfigEntry type alias with API object
# TODO Rename type alias and update all entry annotations
type WattrConfigEntry = ConfigEntry[WattrApi]

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: WattrConfigEntry) -> bool:
    """Set up wattr from a config entry."""
    # TODO 1. Create API instance
    api = WattrApi(hass, entry.data)
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    entry.runtime_data = api

    linked_sensor = entry.data.get(CONF_LINKED_SENSOR)
    # setup linked sensor push if defined
    if linked_sensor:

        async def async_push_sensor_data():
            """Fetch sensor state and push via pushP1Data."""
            state = hass.states.get(linked_sensor)
            if state is None:
                raise UpdateFailed(f"Sensor {linked_sensor} not found")
            try:
                await api.pushP1Data(state.state)
            except Exception as err:
                _LOGGER.exception("Error pushing sensor value")
                raise UpdateFailed from err

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name="wattr_linked_p1_sensor",
            update_method=async_push_sensor_data,
            update_interval=SCAN_INTERVAL,
        )

        await coordinator.async_config_entry_first_refresh()

        if not hasattr(entry, "coordinators"):
            entry.coordinators = {}
        entry.coordinators["linked_p1_sensor"] = coordinator

    # Setup number coordinator
    async def async_update_setpoint():
        """Fetch current setpoint from API."""
        try:
            setpoint = await api.getWaterSetpoint()
            return {"setpoint": setpoint}
        except Exception as err:
            _LOGGER.error("Error fetching setpoint from Wattr API: %s", err)
            raise UpdateFailed from err

    setpoint_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="wattr_setpoint",
        update_method=async_update_setpoint,
        update_interval=SCAN_INTERVAL,
    )
    await setpoint_coordinator.async_config_entry_first_refresh()
    if not hasattr(entry, "coordinators"):
        entry.coordinators = {}
    entry.coordinators["setpoint"] = setpoint_coordinator

    # setup smart mode coordinator
    async def async_update_smart_mode():
        """Fetch current smart mode state from API."""
        try:
            smart_mode = await api.getSmartMode()
            return {"smart_mode": smart_mode}
        except Exception as err:
            _LOGGER.error("Error fetching smart mode from Wattr API: %s", err)
            raise UpdateFailed from err

    smart_mode_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="wattr_smart_mode",
        update_method=async_update_smart_mode,
        update_interval=SCAN_INTERVAL,
    )
    await smart_mode_coordinator.async_config_entry_first_refresh()
    entry.coordinators["smart_mode"] = smart_mode_coordinator

    # Setup relay coordinator
    async def async_update_relays():
        """Fetch current toggle/pulse relay states from the API."""
        try:
            relays = await api.get_toggle_pulse_relays()
            return {"relays": relays}
        except Exception as err:
            _LOGGER.error("Error fetching relays from Wattr API: %s", err)
            raise UpdateFailed from err

    relay_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="wattr_relays",
        update_method=async_update_relays,
        update_interval=SCAN_INTERVAL,
    )
    await relay_coordinator.async_config_entry_first_refresh()
    entry.coordinators["relays"] = relay_coordinator

    # Setup notifications coordinator
    async def async_update_notifications():
        """Fetch current notifications from the API."""
        try:
            notifications = await api.get_notifications()
            return {"notifications": notifications}
        except Exception as err:
            _LOGGER.error("Error fetching notifications from Wattr API: %s", err)
            raise UpdateFailed from err

    notifications_coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="wattr_notifications",
        update_method=async_update_notifications,
        update_interval=SCAN_INTERVAL,
    )
    await notifications_coordinator.async_config_entry_first_refresh()
    entry.coordinators["notifications"] = notifications_coordinator

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: WattrConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
