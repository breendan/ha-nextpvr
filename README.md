# NextPVR Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-blue.svg)](https://hacs.xyz/)
[![Release](https://img.shields.io/github/v/release/breendan/ha-nextpvr?sort=semver)](https://github.com/breendan/ha-nextpvr/releases)
[![Downloads](https://img.shields.io/github/downloads/breendan/ha-nextpvr/total.svg)](https://github.com/breendan/ha-nextpvr/releases)
[![Last Commit](https://img.shields.io/github/last-commit/breendan/ha-nextpvr.svg)](https://github.com/breendan/ha-nextpvr/commits)
[![License](https://img.shields.io/github/license/breendan/ha-nextpvr.svg)](LICENSE)

Monitor NextPVR tuners in Home Assistant. Provides a single binary sensor indicating whether any tuner is in use and one media player entity per tuner with a cleaned title for live TV or recordings.

## Entities

| Entity Type | Description |
|-------------|-------------|
| Binary Sensor: `NextPVR Device In Use` | On if any tuner is Live TV or Recording |
| Media Player (per tuner) | States: playing (LiveTV/Recording), idle, or off; `media_title` parsed from file name |

Media player attributes: `oid`, `status`, `path`.

## Installation

### HACS (Custom Repository)
1. HACS → Integrations → (⋮) Custom repositories.
2. Add `https://github.com/breendan/ha-nextpvr` (Category: Integration).
3. Install “NextPVR Integration”.
4. Restart Home Assistant.

### Manual
1. Copy `custom_components/nextpvr` into `<config>/custom_components/`.
2. Restart Home Assistant.

## Configuration
Settings → Devices & Services → Add Integration → “NextPVR”.

Fields:
- Host (IP / hostname; scheme optional)
- Port (default 8866)
- PIN (NextPVR PIN)
- Use HTTPS (enable if served over TLS)

Adjust polling interval (30–3600s, default 120s) via the integration’s Options.

## Updating
1. Bump `version` in `manifest.json`.
2. Update CHANGELOG.
3. Tag release (e.g. `v1.0.1`).
4. HACS will offer update.

## License
MIT – see [LICENSE](LICENSE).

## Attribution
Not affiliated with the NextPVR project. NextPVR © respective owners.
