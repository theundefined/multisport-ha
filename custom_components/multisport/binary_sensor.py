"""Platform for binary sensor integration."""

from __future__ import annotations

import logging
from typing import List, Optional, cast

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import MultisportDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator: MultisportDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: List[BinarySensorEntity] = []
    # Create binary sensors for each MultiSport card
    for card_id, card_data in coordinator.data.items():
        card_holder_name = (
            f"{card_data['holder_first_name']} {card_data['holder_last_name']}"
        )
        device_name = f"MultiSport {card_holder_name}"

        device_info = DeviceInfo(
            identifiers={(DOMAIN, card_id)},
            name=device_name,
            manufacturer="MultiSport",
            model="Card",
            configuration_url="https://app.kartamultisport.pl/",
            suggested_area="Gym",
        )

        entities.append(
            MultisportUsedTodayBinarySensor(
                coordinator, card_id, device_info, card_holder_name
            )
        )

    async_add_entities(entities)


class MultisportBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base class for MultiSport binary sensors."""

    def __init__(
        self,
        coordinator: MultisportDataUpdateCoordinator,
        card_id: str,
        device_info: DeviceInfo,
        card_holder_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._card_id = card_id
        self._device_info = device_info
        self._card_holder_name = card_holder_name
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return self._device_info

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self._card_id in self.coordinator.data
        )


class MultisportUsedTodayBinarySensor(MultisportBaseBinarySensor):
    """Binary sensor for whether a MultiSport card was used today."""

    _attr_icon = "mdi:dumbbell"  # A gym-related icon
    _attr_translation_key = "used_today"

    def __init__(
        self,
        coordinator: MultisportDataUpdateCoordinator,
        card_id: str,
        device_info: DeviceInfo,
        card_holder_name: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, card_id, device_info, card_holder_name)
        self._attr_unique_id = f"{card_id}_used_today"

    @property
    def is_on(self) -> bool | None:
        """Return True if the binary sensor is on."""
        card_data = self.coordinator.data.get(self._card_id, {})
        return cast(Optional[bool], card_data.get("used_today"))
