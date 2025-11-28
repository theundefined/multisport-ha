"""The MultiSport integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import cast  # Re-import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady

from multisport_py import MultisportClient  # Re-import MultisportClient

from .api import MultisportApi
from .const import (
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    PLATFORMS,
    SERVICE_FORCE_UPDATE,
)
from .coordinator import MultisportDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up MultiSport from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # --- API and Coordinator Setup ---
    api = MultisportApi(
        hass,
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
    )

    if not await api.async_authenticate():
        raise ConfigEntryNotReady("Failed to authenticate with MultiSport.")

    update_interval_minutes = entry.options.get(
        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL.seconds / 60
    )
    update_interval = timedelta(minutes=update_interval_minutes)

    # Cast api.client to MultisportClient because mypy thinks it could be None
    coordinator = MultisportDataUpdateCoordinator(
        hass,
        client=cast(MultisportClient, api.client),
        entry=entry,
        update_interval=update_interval,
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # --- Options Listener ---
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # --- Platform Setup ---
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # --- Service Registration ---
    async def async_force_update(call: ServiceCall) -> None:
        """Handle the service call to force an update."""
        _LOGGER.info("Service 'multisport.force_update' called")
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_FORCE_UPDATE,
        async_force_update,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Get the coordinator from hass.data and close the client session
        coordinator: MultisportDataUpdateCoordinator = hass.data[DOMAIN].pop(
            entry.entry_id
        )
        if coordinator.client:
            await coordinator.client.close()

        # Remove the service
        hass.services.async_remove(DOMAIN, SERVICE_FORCE_UPDATE)

    return cast(bool, unload_ok)  # Cast to bool to satisfy mypy


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug("Handling MultiSport options update")
    coordinator: MultisportDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    update_interval_minutes = entry.options.get(
        CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL.seconds / 60
    )
    coordinator.update_interval = timedelta(minutes=update_interval_minutes)
    _LOGGER.info(
        "MultiSport update interval set to %s minutes", update_interval_minutes
    )
