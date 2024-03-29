"""The APsystems local API integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from time import monotonic

from aiohttp import client_exceptions
from APsystemsEZ1 import APsystemsEZ1M, ReturnOutputData

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.NUMBER, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    hass.data.setdefault(DOMAIN, {})
    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities

    api = APsystemsEZ1M(ip_address=entry.data[CONF_IP_ADDRESS], timeout=8)
    coordinator = ApSystemsDataCoordinator(
        hass, api, interval=entry.data.get(UPDATE_INTERVAL)
    )
    hass.data[DOMAIN][entry.entry_id] = {**entry.data, "COORDINATOR": coordinator}
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener."""
    await hass.config_entries.async_reload(entry.entry_id)


class InverterNotAvailable(Exception):
    pass


class ApSystemsDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, api: APsystemsEZ1M, interval: int = 10):
        """Initialize my coordinator."""
        if interval is None:
            interval = 10
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="APSystems Data",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=interval),
        )
        self.api = api
        self.always_update = True

    async def _async_update_data(self) -> ReturnOutputData | None:
        try:
            data = await self.api.get_output_data()
            return data
        except (TimeoutError, client_exceptions.ClientConnectionError):
            # raise InverterNotAvailable
            raise InverterNotAvailable()

    async def _async_refresh(  # noqa: C901
        self,
        log_failures: bool = True,
        raise_on_auth_failed: bool = False,
        scheduled: bool = False,
        raise_on_entry_error: bool = False,
    ) -> None:
        self._async_unsub_refresh()
        self._debounced_refresh.async_cancel()
        if self._shutdown_requested or scheduled and self.hass.is_stopping:
            return

        if log_timing := self.logger.isEnabledFor(logging.DEBUG):
            start = monotonic()

        auth_failed = False
        previous_update_success = self.last_update_success
        previous_data = self.data
        exc_triggered = False
        try:
            self.data = await self._async_update_data()
        except InverterNotAvailable:
            self.last_update_success = False
            exc_triggered = True
        except Exception as err:  # pylint: disable=broad-except
            self.last_exception = err
            self.last_update_success = False
            self.logger.exception("Unexpected error fetching %s data", self.name)
            exc_triggered = True
        else:
            if not self.last_update_success and not exc_triggered:
                self.last_update_success = True
                self.logger.info("Fetching %s data recovered", self.name)
        finally:
            if log_timing:
                self.logger.debug(
                    "Finished fetching %s data in %.3f seconds (success: %s)",
                    self.name,
                    monotonic() - start,
                    self.last_update_success,
                )
            if not auth_failed and self._listeners and not self.hass.is_stopping:
                self._schedule_refresh()
        if not self.last_update_success and not previous_update_success:
            return
        if (
            self.always_update
            or self.last_update_success != previous_update_success
            or previous_data != self.data
        ):
            self.async_update_listeners()
