"""DataUpdateCoordinator for MultiSport integration."""

from __future__ import annotations

import datetime
import logging
from typing import Any, Dict, List

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from homeassistant.util import dt as dt_util
from multisport_py import AuthenticationError, MultisportClient, MultisportError

_LOGGER = logging.getLogger(__name__)


class MultisportDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching MultiSport data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MultisportClient,
        entry: ConfigEntry,
        update_interval: datetime.timedelta,
    ) -> None:
        """Initialize."""
        self.client = client
        self.entry = entry
        self._last_updated_time: datetime.datetime | None = None
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    @property
    def last_updated_time(self) -> datetime.datetime | None:
        """Return the last successful update time."""
        return self._last_updated_time

    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via MultiSport API."""
        data: Dict[str, Any] = {}
        try:
            # Login should already be handled by config_flow, but ensure it's active
            # Or re-login if token expired (MultisportClient should handle refresh)
            # For simplicity now, we assume client is logged in or can re-login.

            # Fetch main user info to get the main product ID
            user_info = await self.client.get_user_info()
            main_product_id = None
            if user_info and user_info.get("ms_products"):
                main_product_id = user_info["ms_products"][0]

            if not main_product_id:
                raise MultisportError("Could not retrieve main MultiSport product ID.")

            # Fetch authorized users (contains main product and potentially hints for relations)
            authorized_users_data = await self.client.get_authorized_users()

            # Fetch relations (companion cards)
            relations_data = await self.client.get_relations()

            # Consolidate all cards
            all_cards: List[Dict[str, Any]] = []

            # Add main card from authorized_users_data if available
            if authorized_users_data and authorized_users_data.get("products"):
                for product in authorized_users_data["products"]:
                    if product.get("id") == str(
                        main_product_id
                    ):  # Ensure it's the main product
                        all_cards.append(
                            {
                                "id": product["id"],
                                "holder_first_name": product["holder"]["firstName"],
                                "holder_last_name": product["holder"]["lastName"],
                                "is_main": True,
                                "product_type": product.get("productType"),
                                # ... other relevant fields
                            }
                        )
                        break  # Only expect one main card here

            # Add related cards from relations_data
            if relations_data and relations_data.get("items"):
                for item in relations_data["items"]:
                    # Relations might contain different types of items, filter for cards if needed
                    # Assuming items here directly represent cards with similar structure for holder
                    all_cards.append(
                        {
                            "id": item["id"],  # Assuming relations also have an ID
                            "holder_first_name": item["holder"]["firstName"],
                            "holder_last_name": item["holder"]["lastName"],
                            "is_main": False,
                            # ... other relevant fields from relation item
                        }
                    )

            if not all_cards:
                _LOGGER.warning("No MultiSport cards found for the account.")
                # Maybe raise UpdateFailed if no cards are expected ever? For now, empty data is fine.
                data = {}  # Set data to empty explicitly
            else:
                # For each card, fetch limits and history
                for card in all_cards:
                    card_id = card["id"]

                    # Fetch limits
                    limits = await self.client.get_card_limits(card_id)
                    card["remaining_visits"] = limits.get("remainingVisits")

                    # Fetch history (e.g., last 30 days)
                    today = datetime.date.today()
                    thirty_days_ago = today - datetime.timedelta(days=30)
                    history = await self.client.get_card_history(
                        card_id,
                        date_from=thirty_days_ago.isoformat(),
                        date_to=today.isoformat(),
                    )
                    card["history"] = history  # Store full history

                    # Extract last visit details
                    card["last_visit"] = None
                    if history:
                        # History is a list of monthly summaries, each with a 'visits' list
                        # Find the latest visit across all monthly summaries
                        latest_visit_date = None
                        latest_visit_details = None
                        for monthly_summary in history:
                            for visit in monthly_summary.get("visits", []):
                                visit_date_str = visit["date"]  # e.g., "DD-MM-YYYY"
                                visit_time_str = visit["time"]  # e.g., "HH:MM"
                                try:
                                    # Convert to datetime object for comparison
                                    visit_datetime_str = (
                                        f"{visit_date_str} {visit_time_str}"
                                    )
                                    current_visit_datetime = datetime.datetime.strptime(
                                        visit_datetime_str, "%d-%m-%Y %H:%M"
                                    )
                                    if (
                                        latest_visit_date is None
                                        or current_visit_datetime > latest_visit_date
                                    ):
                                        latest_visit_date = current_visit_datetime
                                        latest_visit_details = visit
                                except ValueError:
                                    _LOGGER.warning(
                                        "Could not parse visit date/time: %s %s",
                                        visit_date_str,
                                        visit_time_str,
                                    )

                        if latest_visit_details:
                            card["last_visit"] = latest_visit_details
                            # Add a flag if visit was today
                            if latest_visit_date and latest_visit_date.date() == today:
                                card["used_today"] = True
                            else:
                                card["used_today"] = False
                        else:
                            card["used_today"] = False
                    else:
                        card["used_today"] = False

                    data[card_id] = card  # Store processed card data keyed by card_id

            self._last_updated_time = (
                dt_util.utcnow()
            )  # Set last updated time on success

        except AuthenticationError as exc:
            raise UpdateFailed(
                "Authentication failed. Please re-configure the integration."
            ) from exc
        except MultisportError as exc:
            raise UpdateFailed(
                f"Error communicating with MultiSport API: {exc}"
            ) from exc
        except Exception as exc:  # Catch any other unexpected errors
            _LOGGER.exception("Unexpected error when updating MultiSport data")
            raise UpdateFailed(f"Unexpected error: {exc}") from exc

        return data
