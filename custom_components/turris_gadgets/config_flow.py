"""Config flow for Turris Gadgets."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback

from .connection import DongleConnectionError, async_probe
from .const import (
    CONF_DEBUG_LOGGING,
    CONF_SERIAL_PORT,
    DEFAULT_DEBUG_LOGGING,
    DOMAIN,
    NAME,
)


class TurrisGadgetsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Configure a Turris Dongle."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> TurrisGadgetsOptionsFlow:
        """Return the options flow handler."""
        return TurrisGadgetsOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual setup."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}
        if user_input is not None:
            port = user_input[CONF_SERIAL_PORT]
            debug_logging = user_input[CONF_DEBUG_LOGGING]
            try:
                firmware = await async_probe(port, debug_logging=debug_logging)
            except DongleConnectionError, OSError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"{NAME} ({firmware})",
                    data={
                        CONF_SERIAL_PORT: port,
                        CONF_DEBUG_LOGGING: debug_logging,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SERIAL_PORT, default="/dev/ttyUSB0"): str,
                    vol.Optional(
                        CONF_DEBUG_LOGGING, default=DEFAULT_DEBUG_LOGGING
                    ): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow changing the serial port without removing the integration."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            port = user_input[CONF_SERIAL_PORT]
            debug_logging = entry.options.get(
                CONF_DEBUG_LOGGING,
                entry.data.get(CONF_DEBUG_LOGGING, DEFAULT_DEBUG_LOGGING),
            )
            try:
                await async_probe(port, debug_logging=debug_logging)
            except DongleConnectionError, OSError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_and_abort(
                    entry,
                    data_updates={CONF_SERIAL_PORT: port},
                    reason="reconfigure_successful",
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SERIAL_PORT,
                        default=entry.data[CONF_SERIAL_PORT],
                    ): str
                }
            ),
            errors=errors,
        )


class TurrisGadgetsOptionsFlow(OptionsFlow):
    """Allow settings to be changed after initial setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage Turris Gadgets options."""
        if user_input is not None:
            return self.async_create_entry(
                data={**self.config_entry.options, **user_input}
            )

        current_debug = self.config_entry.options.get(
            CONF_DEBUG_LOGGING,
            self.config_entry.data.get(CONF_DEBUG_LOGGING, DEFAULT_DEBUG_LOGGING),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {vol.Optional(CONF_DEBUG_LOGGING, default=current_debug): bool}
            ),
        )
