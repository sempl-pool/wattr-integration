from __future__ import annotations  # noqa: D100

import logging

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import BASE_URL

_LOGGER = logging.getLogger(__name__)


class WattrApi:
    """Simple API client for Wattr."""

    def __init__(self, hass, config: dict) -> None:
        """Initialize the Wattr API client."""
        self._token = config.get("api_key")
        self._id = config.get("device_id")

        # Use hass-provided session if available
        self._session = async_get_clientsession(hass)
        self._authenticated = False

    async def check_token(self) -> bool:
        """Check if the API key and device ID combination is valid."""
        url = f"{BASE_URL}/api/v1/externalData/validate/{self._id}"
        headers = {
            "Authorization": self._token,
        }

        _LOGGER.debug("Validating token with URL: %s", url)
        _LOGGER.debug("Using device ID: %s", self._id)

        try:
            async with self._session.get(url, headers=headers) as response:
                _LOGGER.debug("Validation response status: %s", response.status)
                if response.status == 200:
                    _LOGGER.debug("Token validation successful")
                    return True
                if response.status == 404:
                    _LOGGER.error("Validation endpoint not found (404). Check if the API server is running and the endpoint exists: %s", url)
                    return False
                _LOGGER.debug("Token validation failed: %s", response.status)
                try:
                    response_text = await response.text()
                    _LOGGER.debug("Response body: %s", response_text)
                except Exception:
                    pass
                return False
        except Exception as e:
            _LOGGER.error("Exception during token validation: %s", e)
            return False

    async def get_waterQuality(self) -> dict:
        """Fetch water quality data from the Wattr API."""

        url = f"{BASE_URL}/api/v1/externalData/waterQuality/{self._id}"
        headers = {"Authorization": self._token}

        async with self._session.get(url, headers=headers) as response:
            if response.status != 200:
                _LOGGER.error("Failed to fetch water quality data: %s", response.status)
                return {}
            return await response.json()

    async def get_waterTemperature(self) -> dict:
        """Fetch water temperature data from the Wattr API."""

        url = f"{BASE_URL}/api/v1/externalData/temperature/{self._id}"
        headers = {"Authorization": self._token}

        async with self._session.get(url, headers=headers) as response:
            if response.status != 200:
                _LOGGER.error(
                    "Failed to fetch water temperature data: %s", response.status
                )
                return {}
            return await response.json()

    async def pushP1Data(self, value: float) -> bool:
        """Push P1 data to the Wattr API."""
        url = f"{BASE_URL}/api/v1/externalControl/setConsumptionSignal/{self._id}"
        headers = {"Authorization": self._token, "Content-Type": "application/json"}
        payload = {"value": float(value)}
        _LOGGER.debug("Pushing P1 data: %s", value)

        try:
            async with self._session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    _LOGGER.error("Failed to send P1 data: %s", resp.status)
                    return False
                _LOGGER.debug("Successfully sent P1 data: %s", value)
                return True
        except Exception as e:
            _LOGGER.error("Exception while sending P1 data: %s", e)
            return False

    async def setWaterSetpoint(self, value: float) -> bool:
        """Set water temperature setpoint via the Wattr API."""
        url = f"{BASE_URL}/api/v1/externalControl/setTemperature/{self._id}"
        headers = {"Authorization": self._token, "Content-Type": "application/json"}
        payload = {"value": float(value)}
        _LOGGER.debug("Setting water temperature setpoint to: %s", value)

        try:
            async with self._session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    _LOGGER.error(
                        "Failed to set water temperature setpoint: %s", resp.status
                    )
                    return False
                _LOGGER.debug(
                    "Successfully set water temperature setpoint to: %s", value
                )
                return True
        except Exception as e:
            _LOGGER.error("Exception while setting water temperature setpoint: %s", e)
            return False

    async def getWaterSetpoint(self) -> float | None:
        """Fetch current water temperature setpoint from the Wattr API."""
        url = f"{BASE_URL}/api/v1/externalControl/getTemperature/{self._id}"
        headers = {"Authorization": self._token}

        try:
            async with self._session.get(url, headers=headers) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to fetch water temperature setpoint: %s",
                        response.status,
                    )
                    return None
                data = await response.json()
                return data.get("setpoint")
        except Exception as e:
            _LOGGER.error("Exception while fetching water temperature setpoint: %s", e)
            return None

    async def setSmartMode(self, enabled: bool) -> bool:
        """Enable or disable smart mode via the Wattr API."""
        url = f"{BASE_URL}/api/v1/externalControl/setMode/{self._id}"
        headers = {"Authorization": self._token, "Content-Type": "application/json"}
        payload = {"smartMode": enabled}
        _LOGGER.debug("Setting smart mode to: %s", enabled)

        try:
            async with self._session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    _LOGGER.error("Failed to set smart mode: %s", resp.status)
                    return False
                _LOGGER.debug("Successfully set smart mode to: %s", enabled)
                return True
        except Exception as e:
            _LOGGER.error("Exception while setting smart mode: %s", e)
            return False

    async def getSmartMode(self) -> bool | None:
        """Fetch current smart mode status from the Wattr API."""
        url = f"{BASE_URL}/api/v1/externalControl/getMode/{self._id}"
        headers = {"Authorization": self._token}

        try:
            async with self._session.get(url, headers=headers) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to fetch smart mode status: %s", response.status
                    )
                    return None
                data = await response.json()
                return data.get("smartMode")
        except Exception as e:
            _LOGGER.error("Exception while fetching smart mode status: %s", e)
            return None
