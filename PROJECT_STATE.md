# Project: multisport-ha

## Goal

Create a Home Assistant custom component for MultiSport, compatible with HACS. The integration will allow users to log in with their credentials and will represent each MultiSport card (main and companion cards) as a separate device in Home Assistant. Each device will have entities displaying information like remaining entries, last visit, etc.

## Plan / TODO List

1.  **[completed]** Project Scaffolding (directory structure, initial files).
2.  **[completed]** Implement Configuration Flow (`config_flow.py`).
3.  **[completed]** Implement DataUpdateCoordinator (`coordinator.py`).
4.  **[completed]** Implement Sensor entities (`sensor.py`).
5.  **[completed]** Implement Binary Sensor entities (`binary_sensor.py`).
6.  **[completed]** Add localization files (`translations/`).
7.  **[completed]** Add CI/CD workflows for testing and validation (`.github/workflows/`).
8.  **[completed]** Final review, linting, and type checking (`black`, `ruff`, `mypy` passed).

## Project Knowledge Base

### Architecture

*   **Pattern**: The integration will use the `DataUpdateCoordinator` pattern for efficient data polling from the cloud.
*   **Authentication**: Configuration will be handled via a UI `ConfigFlow`. It will ask for username and password and validate them by attempting a login with `multisport-py`.
*   **Device Model**: Each MultiSport card associated with an account (main and related) will be created as a separate `Device` in Home Assistant. This provides a clear separation and allows per-card automations.

### Implemented Features and Fixes

*   **`multisport-py` Release Strategy**: Implemented tag-based release strategy in `multisport-py` with `release.sh` and updated CI.
*   **Blocking Call Fix**: Introduced `custom_components/multisport/api.py` with `MultisportApi` class to handle blocking `MultisportClient` instantiation and authentication, resolving "blocking call" warnings.
*   **"Not Logged In" Error Fix**: Refactored `__init__.py` and `config_flow.py` to correctly use `MultisportApi` for authentication, ensuring the client passed to the coordinator is logged in.
*   **Configurable Update Interval**: Implemented an Options Flow in `config_flow.py` and `__init__.py` to allow users to set the update interval (defaulting to 1 hour).
*   **Force Update Service**: Added `multisport.force_update` service in `__init__.py` and described it in `services.yaml` for on-demand data refresh.
*   **Localization**: Entity names are now localized to Polish and English using `_attr_translation_key` and updated translation files (`en.json`, `pl.json`). This includes specific translation for "Remaining Visits this Month".
*   **Last Updated Diagnostic Sensor**: Added a new diagnostic sensor in `sensor.py` that displays the `last_updated_time` from the coordinator.
*   **Type Checking & Linting**: All `mypy` errors (including previous `AttributeError` and `Name not defined`), `ruff` warnings, and `black` formatting issues are resolved.
*   **Development Setup**: Added a `.gitignore` file for the `multisport-ha` project to exclude unnecessary files from version control.