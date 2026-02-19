---
trigger: always_on
---

# ha-remi Integration Rules

## Project Overview

Unofficial Home Assistant custom integration for the UrbanHello Remi smart alarm clock.
Uses the Parse Server-based cloud API at `https://remi2.urbanhello.com`.

## Stack

- Python 3.12+
- Home Assistant custom integration (no external Python dependencies — uses built-in `aiohttp` from HA)
- Parse Server REST API (cloud polling, 60s interval)

## File Structure

```text
custom_components/remi/
├── __init__.py           # Entry setup, platform forwarding, alarm CRUD services
├── manifest.json         # Integration metadata (domain: remi, version: semver)
├── config_flow.py        # UI config flow — username + password only
├── const.py              # All constants: API URL, app ID, face/music mappings
├── coordinator.py        # RemiDataUpdateCoordinator — polls Remi + Event APIs
├── api.py                # RemiApiClient — all HTTP calls, auto re-auth on 401
├── entity.py             # RemiEntity base class (CoordinatorEntity + DeviceInfo)
├── sensor.py             # Read-only sensors
├── binary_sensor.py      # Online, alive, firmware update
├── select.py             # Clock face, clock format, music mode
├── number.py             # Volume, noise threshold
├── light.py              # Night light + background color (RGB)
├── services.yaml         # Alarm CRUD service definitions
├── strings.json          # UI strings
└── translations/en.json  # English translations
```

## API

- **Base URL**: `https://remi2.urbanhello.com` (hardcoded in `const.py`)
- **App ID**: `jf1a0bADt5fq` (hardcoded, required on all requests)
- **Auth**: `POST /parse/login` → `sessionToken` + `currentRemi.objectId`
- **Session header**: `X-Parse-Session-Token`
- **Re-auth**: automatic on 401 response in `api.py`
- **Multiple devices per account**: login response returns `remis` (array of objectIds) and `currentRemi` (active device pointer)
- **Device selection**: config flow shows a `device` step only when `len(remis) > 1`; single-device accounts skip it
- **One config entry per device**: `remi_id` used as unique ID; adding the same device twice is aborted

## Key Data Mappings

### Temperature

- API field: `temp` (integer)
- Formula: `(temp - 115) / 2` → °C
- Example: `temp=157` → `21.0°C`

### Clock Faces

| define | objectId | Display name |
|---|---|---|
| FACE_OFF | GDaZOVdRqj | Off |
| FACE_DAY | fIjF0yWRxX | Awake |
| FACE_NIGHT | rnAltoFwYC | Sleepy |
| FACE_SEMI_AWAKE | 9faiiPGBVv | Semi-Awake |
| FACE_SMILY | d712mdpZ0v | Smiley |

### RGB Light Fields

- `lightnight` → Night Light entity
- `background_color` → Background Color entity
- Both stored as `[R, G, B]` arrays; turn off = `[0, 0, 0]`

### Alarm Events

- Class: `Event` on Parse Server
- Linked to device via `remi` Pointer
- CRUD via services: `remi.create_alarm`, `remi.update_alarm`, `remi.delete_alarm`
- Field names (`name`, `time`, `enabled`, `repeat`, `face`, `volume`) are inferred — verify against real API response when available

## Coding Standards

- All files use `from __future__ import annotations`
- Follow Home Assistant coding standards and entity patterns
- Use `DataUpdateCoordinator` — never poll directly in entity properties
- Entity unique IDs: `{remi_id}_{key}`
- All writes call `coordinator.async_request_refresh()` after the API call
- No hardcoded credentials or tokens in source files
- Keep `const.py` as the single source of truth for all constants and mappings

## Versioning

- Version in `manifest.json` must match the GitHub release tag (semver, e.g. `0.1.0`)
- Current version: `0.1.0`
