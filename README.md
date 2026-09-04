# Quick Dutch Basemap

A QGIS plugin that adds a one-click toolbar button for loading PDOK's Dutch
aerial photo ("luchtfoto") WMS basemaps into your project — no more manually
walking through **Layer → Add Layer → Add WMS/WMTS Layer** every time.

## Features

- Dedicated toolbar with a single icon.
- Click the icon to get an instant dropdown list of all available luchtfoto
  layers (Actueel, and historical years back to 2016).
- Click a layer name and it loads immediately — no OK button, no extra
  dialogs.
- Layers are grouped by resolution: all **8cm** layers first, then all
  **25cm** layers, with the newest year first within each group.
- The layer list is fetched once per QGIS session directly from PDOK's
  `GetCapabilities`, so new years PDOK adds in the future show up
  automatically without a plugin update.
- Layers are always loaded in **EPSG:28992** (Amersfoort / RD New), labeled
  in the Layers panel with their full title (e.g. "Luchtfoto 2023 Ortho 8cm
  RGB").

## Data source

Imagery is served by [PDOK](https://www.pdok.nl/) (Publieke Dienstverlening
Op de Kaart), the Dutch national geo-data platform, via the
`luchtfotorgb` WMS service:

```
https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0
```

## Installation

1. Download the latest release (or clone this repository).
2. Copy the `quick-dutch-basemap` folder into your QGIS plugins directory:
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux / macOS:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
3. In QGIS, open **Plugins → Manage and Install Plugins**, find
   **Quick Dutch Basemap** in the installed list, and enable it.

## Usage

Click the **Quick Dutch Basemap** icon in its toolbar, then click any layer
in the dropdown — it loads into the current project instantly.

## Requirements

- QGIS 3.16 – 3.99
- An internet connection (to fetch the layer list and the WMS tiles)

## License

MIT — see [LICENSE](LICENSE).

## Author

**MD Moinul Mobin**
Email: mdmoinulmobin@gmail.com
LinkedIn: [linkedin.com/in/mdmoinulmobin](https://www.linkedin.com/in/mdmoinulmobin/)
GitHub: [github.com/md-moinul-mobin](https://github.com/md-moinul-mobin)
