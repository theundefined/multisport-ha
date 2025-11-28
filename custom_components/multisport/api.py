"""API for MultiSport integration."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

from multisport_py import (
    AuthenticationError,
    MultisportClient,
    MultisportError,
)

_LOGGER = logging.getLogger(__name__)


class MultisportApi:
    """A wrapper for the MultisportClient to handle blocking calls and authentication."""

    def __init__(self, hass: HomeAssistant, username: str, password: str) -> None:
        """Initialize the API wrapper."""
        self._hass = hass
        self._username = username
        self._password = password
        self.client: MultisportClient | None = None

    async def async_authenticate(self) -> bool:
        """
        Authenticate with the MultiSport API.

        This handles the blocking instantiation of the client and the async login.
        Returns True on success, False on failure.
        """
        _LOGGER.debug("Authenticating with MultiSport API")
        try:
            # The constructor of MultisportClient might be blocking.
            self.client = await self._hass.async_add_executor_job(
                self._blocking_create_client
            )

            # The login method is async, so we can await it directly.
            await self.client.login()

        except (AuthenticationError, MultisportError) as exc:
            _LOGGER.error("Failed to authenticate with MultiSport: %s", exc)
            if self.client:
                await self.client.close()
            return False
        except Exception:
            _LOGGER.exception("Unexpected error during authentication")
            if self.client:
                await self.client.close()
            return False

        return True

    def _blocking_create_client(self) -> MultisportClient:
        """Create the MultisportClient instance in a blocking-safe way."""
        return MultisportClient(username=self._username, password=self._password)
