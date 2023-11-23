import asyncio

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_IP_ADDRESS, CONF_NAME
from APsystemsEZ1 import APsystemsEZ1M
from aiohttp import client_exceptions

from .const import DOMAIN, LOGGER


DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_IP_ADDRESS): str,
        vol.Required(CONF_NAME): str,
        vol.Optional("check", default=True): bool
    }
)

class APsystemsLocalAPIFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
            self,
            user_input: dict | None = None,
    ) -> config_entries.FlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}

        if user_input is not None:
            try:
                if user_input["check"]:
                    api = APsystemsEZ1M(user_input[CONF_IP_ADDRESS])
                    await api.get_device_info()
            except (client_exceptions.ClientConnectionError, asyncio.TimeoutError) as exception:
                LOGGER.warning(exception)
                _errors["base"] = "connection_refused"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=_errors,
        )
