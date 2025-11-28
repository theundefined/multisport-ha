from __future__ import annotations

import logging
from typing import Any, List, Optional, cast

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
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
    """Set up the sensor platform."""
    coordinator: MultisportDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: List[SensorEntity] = []
    # Create sensors for each MultiSport card
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

        entities.extend(
            [
                MultisportRemainingVisitsSensor(
                    coordinator, card_id, device_info, card_holder_name
                ),
                MultisportLastVisitSensor(
                    coordinator, card_id, device_info, card_holder_name
                ),
                MultisportLastUpdatedSensor(
                    coordinator, card_id, device_info, card_holder_name
                ),
            ]
        )

    async_add_entities(entities)


class MultisportBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for MultiSport sensors."""

    def __init__(
        self,
        coordinator: MultisportDataUpdateCoordinator,
        card_id: str,
        device_info: DeviceInfo,
        card_holder_name: str,
    ) -> None:
        """Initialize the sensor."""
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


class MultisportRemainingVisitsSensor(MultisportBaseSensor):
    """Sensor for remaining visits on a MultiSport card."""

    _attr_native_unit_of_measurement = "visits"
    _attr_icon = "mdi:ticket-confirmation"
    _attr_translation_key = "remaining_visits"

    def __init__(
        self,
        coordinator: MultisportDataUpdateCoordinator,
        card_id: str,
        device_info: DeviceInfo,
        card_holder_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, card_id, device_info, card_holder_name)
        self._attr_unique_id = f"{card_id}_remaining_visits"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        card_data = self.coordinator.data.get(self._card_id, {})
        return cast(Optional[int], card_data.get("remaining_visits"))


class MultisportLastVisitSensor(MultisportBaseSensor):
    """Sensor for the last visit on a MultiSport card."""

    _attr_icon = "mdi:map-marker-distance"
    _attr_translation_key = "last_visit"
    _attr_extra_state_attributes: dict[str, Any] = {}

    def __init__(
        self,
        coordinator: MultisportDataUpdateCoordinator,
        card_id: str,
        device_info: DeviceInfo,
        card_holder_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, card_id, device_info, card_holder_name)
        self._attr_unique_id = f"{card_id}_last_visit"
        self._attr_extra_state_attributes = {}

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        card_data = self.coordinator.data.get(self._card_id, {})
        last_visit = card_data.get("last_visit")
        if last_visit:
            facility_name = last_visit.get("facilityName")
            visit_date = last_visit.get("date")
            visit_time = last_visit.get("time")

            # Update extra state attributes
            self._attr_extra_state_attributes = {
                "date": visit_date,
                "time": visit_time,
                "registration_method": last_visit.get("registrationMethod"),
                "place": facility_name,
            }

            # Format the native value
            if (
                isinstance(facility_name, str)
                and isinstance(visit_date, str)
                and isinstance(visit_time, str)
            ):
                return f"{facility_name} {visit_date} {visit_time}"
            elif isinstance(facility_name, str):
                return facility_name

        # If no last_visit, or if parts are missing, ensure attributes are reset and return None
        self._attr_extra_state_attributes = {}
        return None


class MultisportLastUpdatedSensor(MultisportBaseSensor):
    """Diagnostic sensor for the last successful update time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "last_updated"

    def __init__(
        self,
        coordinator: MultisportDataUpdateCoordinator,
        card_id: str,
        device_info: DeviceInfo,
        card_holder_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, card_id, device_info, card_holder_name)
        self._attr_unique_id = f"{card_id}_last_updated"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.last_updated_time
