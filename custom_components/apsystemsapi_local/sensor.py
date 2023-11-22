from __future__ import annotations

import asyncio
from dataclasses import dataclass
from collections.abc import Callable, Coroutine
from aiohttp import client_exceptions

import voluptuous as vol

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    PLATFORM_SCHEMA
)
import homeassistant.helpers.config_validation as cv
from homeassistant.const import UnitOfPower, UnitOfEnergy
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from .apsystems_local_api import APsystemsEZ1M
from homeassistant.helpers.device_registry import DeviceInfo

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_IP_ADDRESS): cv.string,
    vol.Optional(CONF_NAME, default="solar"): cv.string
})


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    api = APsystemsEZ1M(ip_address=config[CONF_IP_ADDRESS])

    sensors = [
        PowerSensorTotal(api, device_name=config[CONF_NAME], sensor_name="Total Power", sensor_id="total_power"),
        Panel1PowerSensor(api, device_name=config[CONF_NAME], sensor_name="Panel 1 Power", sensor_id="panel_1_power"),
        Panel2PowerSensor(api, device_name=config[CONF_NAME], sensor_name="Panel 2 Power", sensor_id="panel_2_power"),
        Panel1LifetimeEnergy(api, device_name=config[CONF_NAME], sensor_name="Panel 1 Lifetime Production",
                             sensor_id="panel_1_lifetime_production"),
        Panel2LifetimeEnergy(api, device_name=config[CONF_NAME], sensor_name="Panel 2 Lifetime Production",
                             sensor_id="panel_2_lifetime_production"),
        Panel1TodayEnergy(api, device_name=config[CONF_NAME], sensor_name="Panel 1 Today Production",
                          sensor_id="panel_1_today_production"),
        Panel2TodayEnergy(api, device_name=config[CONF_NAME], sensor_name="Panel 2 Today Production",
                          sensor_id="panel_2_today_production"),
        LifetimeEnergy(api, device_name=config[CONF_NAME], sensor_name="Lifetime Production",
                       sensor_id="lifetime_production"),
        TodayEnergy(api, device_name=config[CONF_NAME], sensor_name="Today Production",
                    sensor_id="today_production")]

    add_entities(sensors, True)


class BaseSensor(SensorEntity):
    """Representation of an APsystem sensor."""
    _attr_available = True

    def __init__(self, api: APsystemsEZ1M, device_name: str, sensor_name: str, sensor_id: str):
        """Initialize the sensor."""
        self._api = api
        self._state = None
        self._device_name = device_name
        self._sensor_name = sensor_name
        self._sensor_id = sensor_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"APsystems {self._device_name} {self._sensor_name}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unique_id(self) -> str | None:
        return f"apsystemsapi_{self._device_name}_{self._sensor_id}"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={
                ("apsystemsapi_local", self._device_name)
            },
            name=self._device_name,
            manufacturer="APsystems",
            model="EZ1-M",
        )


class BasePowerSensor(BaseSensor):
    _device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT


class PowerSensorTotal(BasePowerSensor):
    async def async_update(self):
        try:
            self._state = await self._api.get_total_output()
            self._attr_available = True
        except client_exceptions.ClientConnectionError:
            self._attr_available = False


class Panel1PowerSensor(BasePowerSensor):
    async def async_update(self):
        try:
            self._state = (await self._api.get_output_data()).p1
            self._attr_available = True
        except client_exceptions.ClientConnectionError:
            self._attr_available = False


class Panel2PowerSensor(BasePowerSensor):
    async def async_update(self):
        try:
            self._state = (await self._api.get_output_data()).p2
            self._attr_available = True
        except client_exceptions.ClientConnectionError:
            self._attr_available = False


class BaseEnergySensor(BaseSensor):
    _device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY


class LifetimeEnergy(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL

    async def async_update(self):
        try:
            self._state = await self._api.get_total_energy_lifetime()
            self._attr_available = True
        except client_exceptions.ClientConnectionError:
            self._attr_available = False


class Panel1LifetimeEnergy(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL

    async def async_update(self):
        try:
            self._state = (await self._api.get_output_data()).te1
            self._attr_available = True
        except client_exceptions.ClientConnectionError:
            self._attr_available = False


class Panel2LifetimeEnergy(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL

    async def async_update(self):
        try:
            self._state = (await self._api.get_output_data()).te2
            self._attr_available = True
        except client_exceptions.ClientConnectionError:
            self._attr_available = False


class Panel1TodayEnergy(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    async def async_update(self):
        try:
            self._state = (await self._api.get_output_data()).e1
            self._attr_available = True
        except client_exceptions.ClientConnectionError:
            self._attr_available = False


class Panel2TodayEnergy(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    async def async_update(self):
        try:
            self._state = (await self._api.get_output_data()).e2
            self._attr_available = True
        except client_exceptions.ClientConnectionError:
            self._attr_available = False


class TodayEnergy(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    async def async_update(self):
        try:
            self._state = await self._api.get_total_energy_today()
            self._attr_available = True
        except client_exceptions.ClientConnectionError:
            self._attr_available = False
