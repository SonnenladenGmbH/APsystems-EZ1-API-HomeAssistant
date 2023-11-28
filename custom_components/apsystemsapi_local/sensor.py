from __future__ import annotations

import asyncio

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from aiohttp import client_exceptions
from APsystemsEZ1 import APsystemsEZ1M
from homeassistant import config_entries
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType

from .const import DOMAIN

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Optional(CONF_NAME, default="solar"): cv.string,
    }
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    api = APsystemsEZ1M(ip_address=config[CONF_IP_ADDRESS])

    sensors = [
        PowerSensorTotal(
            api,
            device_name=config[CONF_NAME],
            sensor_name="Total Power",
            sensor_id="total_power",
        ),
        PowerSensorTotalP1(
            api,
            device_name=config[CONF_NAME],
            sensor_name="Total Power P1",
            sensor_id="total_power_p1",
        ),
        PowerSensorTotalP2(
            api,
            device_name=config[CONF_NAME],
            sensor_name="Total Power P2",
            sensor_id="total_power_p2",
        ),
        LifetimeEnergy(
            api,
            device_name=config[CONF_NAME],
            sensor_name="Lifetime Production",
            sensor_id="lifetime_production",
        ),
        LifetimeEnergyP1(
            api,
            device_name=config[CONF_NAME],
            sensor_name="Lifetime Production P1",
            sensor_id="lifetime_production_p1",
        ),
        LifetimeEnergyP2(
            api,
            device_name=config[CONF_NAME],
            sensor_name="Lifetime Production P2",
            sensor_id="lifetime_production_p2",
        ),
        TodayEnergy(
            api,
            device_name=config[CONF_NAME],
            sensor_name="Today Production",
            sensor_id="today_production",
        ),
        TodayEnergyP1(
            api,
            device_name=config[CONF_NAME],
            sensor_name="Today Production P1",
            sensor_id="today_production_p1",
        ),
        TodayEnergyP2(
            api,
            device_name=config[CONF_NAME],
            sensor_name="Today Production_p2",
            sensor_id="today_production_p2",
        ),
    ]

    add_entities(sensors, True)


class BaseSensor(SensorEntity):
    """Representation of an APsystem sensor."""

    _attr_available = False

    def __init__(
        self, api: APsystemsEZ1M, device_name: str, sensor_name: str, sensor_id: str
    ):
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
            identifiers={("apsystemsapi_local", self._device_name)},
            name=self._device_name,
            manufacturer="APsystems",
            model="EZ1-M",
        )

    async def async_update_data(self):
        try:
            data = await self._api.get_output_data()
            self.update_state(data)
            self._attr_available = False
        except (client_exceptions.ClientConnectionError, asyncio.TimeoutError):
            self._attr_available = False

    def update_state(self, data):
        raise NotImplementedError("Must be implemented by subclasses.")


class BasePowerSensor(BaseSensor):
    _device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT


class PowerSensorTotal(BasePowerSensor):
    def update_state(self, data):
        self._state = data.p1 + data.p2

    async def async_update(self):
        await self.async_update_data()


class PowerSensorTotalP1(BasePowerSensor):
    def update_state(self, data):
        self._state = data.p1

    async def async_update(self):
        await self.async_update_data()


class PowerSensorTotalP2(BasePowerSensor):
    def update_state(self, data):
        self._state = data.p2

    async def async_update(self):
        await self.async_update_data()


class BaseEnergySensor(BaseSensor):
    _device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY


class LifetimeEnergy(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL

    def update_state(self, data):
        self._state = data.te1 + data.te2

    async def async_update(self):
        await self.async_update_data()


class LifetimeEnergyP1(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL

    def update_state(self, data):
        self._state = data.te1

    async def async_update(self):
        await self.async_update_data()


class LifetimeEnergyP2(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL

    def update_state(self, data):
        self._state = data.te2

    async def async_update(self):
        await self.async_update_data()


class TodayEnergy(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def update_state(self, data):
        self._state = data.e1 + data.e2

    async def async_update(self):
        await self.async_update_data()


class TodayEnergyP1(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def update_state(self, data):
        self._state = data.e1

    async def async_update(self):
        await self.async_update_data()


class TodayEnergyP2(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def update_state(self, data):
        self._state = data.e2

    async def async_update(self):
        await self.async_update_data()
