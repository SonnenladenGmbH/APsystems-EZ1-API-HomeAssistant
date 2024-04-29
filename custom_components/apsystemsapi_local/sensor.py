from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import datetime as dt
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ApSystemsDataCoordinator
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
    coordinator = config["COORDINATOR"]

    sensors = [
        PowerSensorTotal(
            coordinator,
            device_name=config[CONF_NAME],
            sensor_name="Total Power",
            sensor_id="total_power",
        ),
        PowerSensorTotalP1(
            coordinator,
            device_name=config[CONF_NAME],
            sensor_name="Power P1",
            sensor_id="total_power_p1",
        ),
        PowerSensorTotalP2(
            coordinator,
            device_name=config[CONF_NAME],
            sensor_name="Power P2",
            sensor_id="total_power_p2",
        ),
        LifetimeEnergy(
            coordinator,
            device_name=config[CONF_NAME],
            sensor_name="Lifetime Production",
            sensor_id="lifetime_production",
        ),
        LifetimeEnergyP1(
            coordinator,
            device_name=config[CONF_NAME],
            sensor_name="Lifetime Production P1",
            sensor_id="lifetime_production_p1",
        ),
        LifetimeEnergyP2(
            coordinator,
            device_name=config[CONF_NAME],
            sensor_name="Lifetime Production P2",
            sensor_id="lifetime_production_p2",
        ),
        TodayEnergy(
            coordinator,
            device_name=config[CONF_NAME],
            sensor_name="Today Production",
            sensor_id="today_production",
        ),
        TodayEnergyP1(
            coordinator,
            device_name=config[CONF_NAME],
            sensor_name="Today Production P1",
            sensor_id="today_production_p1",
        ),
        TodayEnergyP2(
            coordinator,
            device_name=config[CONF_NAME],
            sensor_name="Today Production P2",
            sensor_id="today_production_p2",
        ),
    ]

    add_entities(sensors)


class BaseSensor(CoordinatorEntity, SensorEntity):
    """Representation of an APsystem sensor."""

    def __init__(
        self,
        coordinator: ApSystemsDataCoordinator,
        device_name: str,
        sensor_name: str,
        sensor_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._state = None
        self._device_name = device_name
        self._sensor_name = sensor_name
        self._sensor_id = sensor_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._device_name} {self._sensor_name}"

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

    #     @callback
    # def _handle_coordinator_update(self):
    #     raise NotImplementedError("Must be implemented by subclasses.")


class BasePowerSensor(BaseSensor):
    _device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT


class PowerSensorTotal(BasePowerSensor):
    @callback
    def _handle_coordinator_update(self):
        if self.coordinator.data is not None:
            self._state = self.coordinator.data.p1 + self.coordinator.data.p2
        self.async_write_ha_state()


class PowerSensorTotalP1(BasePowerSensor):
    @callback
    def _handle_coordinator_update(self):
        if self.coordinator.data is not None:
            self._state = self.coordinator.data.p1
        self.async_write_ha_state()


class PowerSensorTotalP2(BasePowerSensor):
    @callback
    def _handle_coordinator_update(self):
        if self.coordinator.data is not None:
            self._state = self.coordinator.data.p2
        self.async_write_ha_state()


class BaseEnergySensor(BaseSensor):
    _device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY

    def __init__(
        self, coordinator: ApSystemsDataCoordinator, device_name, sensor_name, sensor_id
    ):
        super().__init__(coordinator, device_name, sensor_name, sensor_id)
        self._old_state: float = 0
        self._base_state: float = 0
        self._last_update: int = 0

    def debounce(self, new_state):
        try:
            if self._old_state > new_state:
                self._base_state = self._base_state + self._old_state
        except TypeError:
            pass

        self._old_state = new_state

        # reset basis each day
        if self._last_update != dt.now().day:
            self._last_update = dt.now().day
            self._base_state = 0

        if isinstance(new_state, (int, float)):
            return new_state + self._base_state

        return new_state


class LifetimeEnergy(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL

    @callback
    def _handle_coordinator_update(self):
        if self.coordinator.data is not None:
            self._state = self.coordinator.data.te1 + self.coordinator.data.te2
        self.async_write_ha_state()


class LifetimeEnergyP1(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL

    @callback
    def _handle_coordinator_update(self):
        if self.coordinator.data is not None:
            self._state = self.coordinator.data.te1
        self.async_write_ha_state()


class LifetimeEnergyP2(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL

    @callback
    def _handle_coordinator_update(self):
        if self.coordinator.data is not None:
            self._state = self.coordinator.data.te2
        self.async_write_ha_state()


class TodayEnergy(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @callback
    def _handle_coordinator_update(self):
        if self.coordinator.data is not None:
            self._state = self.debounce(
                self.coordinator.data.e1 + self.coordinator.data.e2
            )
        self.async_write_ha_state()


class TodayEnergyP1(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @callback
    def _handle_coordinator_update(self):
        if self.coordinator.data is not None:
            self._state = self.debounce(self.coordinator.data.e1)
        self.async_write_ha_state()


class TodayEnergyP2(BaseEnergySensor):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @callback
    def _handle_coordinator_update(self):
        if self.coordinator.data is not None:
            self._state = self.debounce(self.coordinator.data.e2)
        self.async_write_ha_state()
