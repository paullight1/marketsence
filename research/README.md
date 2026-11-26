# Third-party geospatial source workspace

This directory is an isolated **research and audit workspace**, not production application code. It tracks 10 upstream projects useful to an Evolve location-intelligence product.

## Quick start

```bash
bash research/scripts/clone-upstreams.sh
```

The script fetches the real repositories from GitHub into `research/upstreams/<slug>`, checks out each at its pinned SHA, and does not overwrite existing checkouts. It requires Git and an internet connection.

**Important:** Adding this manifest and clone script to GitHub does **not** clone the source code into this repository. The script must run on a machine or CI runner with outbound GitHub access. Local cloned repositories are excluded from the parent repository to avoid accidentally mixing software and licenses.

## Sources and assessed roles

| Project | Purpose | Upstream |
| --- | --- | --- |
| marketlens | Commercial market-analysis reference | [GipsyDanger-dev/MarketLens](https://github.com/GipsyDanger-dev/MarketLens) |
| geolibre | Web GIS and geospatial analysis | [opengeos/GeoLibre](https://github.com/opengeos/GeoLibre) |
| geoagent | AI GIS agent framework | [opengeos/GeoAgent](https://github.com/opengeos/GeoAgent) |
| geolens | Spatial data platform | [geolens-io/geolens](https://github.com/geolens-io/geolens) |
| goat | Accessibility and urban planning (GPL isolation required) | [plan4better/goat](https://github.com/plan4better/goat) |
| osmnx | Street-network analysis | [gboeing/osmnx](https://github.com/gboeing/osmnx) |
| valhalla | Routing engine | [valhalla/valhalla](https://github.com/valhalla/valhalla) |
| geoai | Remote sensing / satellite ML | [opengeos/geoai](https://github.com/opengeos/geoai) |
| overturemaps-py | Overture Maps data toolkit | [OvertureMaps/overturemaps-py](https://github.com/OvertureMaps/overturemaps-py) |
| geo-fence | Huff gravity-model prototype | [jackson-marcus/Geo-Fence](https://github.com/jackson-marcus/Geo-Fence) |

See `source-manifest.json` for pinned revisions and license flags.

## Before integrating upstream code

1. Audit the actual checked-out code, dependencies, secrets, vulnerabilities, and runtime suitability.
2. Verify license files and attribution for every project and its dependencies; **GOAT is GPL-3.0** and should stay separately evaluated unless legal review approves integration. Valhalla and Geo-Fence require explicit license verification.
3. Avoid dumping upstream repositories into the core application; select audited components and interfaces.
4. Build Evolve's proprietary investment suitability, data provenance, confidence and financial modelling layers separately.
5. Respect map and dataset terms, especially data storage restrictions and commercial use.

This work does not modify existing MarketSense features or product code.
