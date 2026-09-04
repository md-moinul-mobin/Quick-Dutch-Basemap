# -*- coding: utf-8 -*-
"""
Quick Dutch Basemap
--------------------
Adds a single toolbar button that:
  1. Fetches the current WMS GetCapabilities document from PDOK's
     "luchtfotorgb" aerial photo service.
  2. Shows a combo-box dialog of the available layer titles.
  3. Loads the chosen layer into the current project instantly,
     in EPSG:28992, labeled with its human-readable title.

Author: MD Moinul Mobin
"""

import os
import re
import urllib.request
import xml.etree.ElementTree as ET

from qgis.PyQt.QtCore import QUrl, QThread, pyqtSignal
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu, QToolButton, QMessageBox

from qgis.core import QgsProject, QgsRasterLayer

WMS_BASE_URL = "https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0"
WMS_VERSION = "1.3.0"
TARGET_CRS = "EPSG:28992"

# XML namespace used in WMS 1.3.0 capabilities documents
WMS_NS = {"wms": "http://www.opengis.net/wms"}

# Turns "Luchtfoto 2023 Ortho 8cm RGB" into "2023 · 8cm"
SHORT_LABEL_RE = re.compile(r"^Luchtfoto\s+(.*?)\s+Ortho\s+(.*?cm)\s+RGB$")

MENU_QSS = """
QMenu {
    background-color: #ffffff;
    border: 1px solid #c9c9c9;
    border-radius: 6px;
    padding: 2px 0px;
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 9pt;
}
QMenu::item {
    padding: 2px 16px 2px 10px;
    color: #222222;
}
QMenu::item:selected {
    background-color: #21468b;
    color: #ffffff;
}
QMenu::item:disabled {
    color: #8a8a8a;
    font-weight: bold;
    font-family: "Segoe UI", "Noto Sans", sans-serif;
    font-size: 7.5pt;
    padding-top: 3px;
    padding-bottom: 1px;
}
QMenu::separator {
    height: 1px;
    background: #dddddd;
    margin: 2px 6px;
}
"""


def _short_label(title):
    match = SHORT_LABEL_RE.match(title)
    if match:
        return f"{match.group(1)} · {match.group(2)}"
    return title


def _download_and_parse_capabilities():
    """Fetch + parse GetCapabilities. Runs on a background thread.
    Returns a list of (title, name) tuples. Raises on failure.
    """
    capabilities_url = (
        f"{WMS_BASE_URL}?service=WMS&request=GetCapabilities"
        f"&version={WMS_VERSION}"
    )
    with urllib.request.urlopen(capabilities_url, timeout=15) as response:
        xml_bytes = response.read()

    root = ET.fromstring(xml_bytes)
    layers = []
    for layer_el in root.iter("{http://www.opengis.net/wms}Layer"):
        name_el = layer_el.find("wms:Name", WMS_NS)
        title_el = layer_el.find("wms:Title", WMS_NS)
        if name_el is None or title_el is None:
            continue
        name = (name_el.text or "").strip()
        title = (title_el.text or "").strip()
        if name and title:
            layers.append((title, name))
    return layers


class CapabilitiesFetcher(QThread):
    """Fetches the layer list on a background thread so QGIS never blocks."""

    finished_ok = pyqtSignal(list)
    finished_error = pyqtSignal(str)

    def run(self):
        try:
            layers = _download_and_parse_capabilities()
            self.finished_ok.emit(layers)
        except Exception as exc:  # network error, parse error, etc.
            self.finished_error.emit(str(exc))


class QuickDutchBasemap:
    """QGIS plugin implementation."""

    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.action = None
        self.toolbar = None
        self.tool_button = None
        self.menu = None
        self.layers_cache = None   # None = not loaded yet, [] = load failed
        self.fetcher = None

    # ------------------------------------------------------------------
    # QGIS plugin lifecycle
    # ------------------------------------------------------------------

    def initGui(self):
        icon_path = os.path.join(self.plugin_dir, "dutch_basemap.png")

        self.menu = QMenu(self.iface.mainWindow())
        self.menu.setStyleSheet(MENU_QSS)
        self.menu.aboutToShow.connect(self._populate_menu)

        self.tool_button = QToolButton(self.iface.mainWindow())
        self.tool_button.setIcon(QIcon(icon_path))
        self.tool_button.setText("Quick Dutch Basemap")
        self.tool_button.setToolTip(
            "Load a PDOK Dutch aerial photo (luchtfoto) WMS basemap"
        )
        self.tool_button.setPopupMode(QToolButton.InstantPopup)
        self.tool_button.setMenu(self.menu)

        # Dedicated toolbar, as requested, rather than reusing an existing one.
        self.toolbar = self.iface.addToolBar("Quick Dutch Basemap")
        self.toolbar.setObjectName("QuickDutchBasemapToolbar")
        self.toolbar.addWidget(self.tool_button)

        # Keep a QAction too, so the plugin still shows up in the Web menu.
        self.action = QAction(QIcon(icon_path), "Quick Dutch Basemap", self.iface.mainWindow())
        self.action.setMenu(self.menu)
        self.iface.addPluginToWebMenu("&Quick Dutch Basemap", self.action)

        # One-time background fetch, kicked off as soon as the plugin loads.
        self._start_fetch()

    def unload(self):
        if self.action is not None:
            self.iface.removePluginWebMenu("&Quick Dutch Basemap", self.action)
        if self.toolbar is not None:
            del self.toolbar
        if self.fetcher is not None and self.fetcher.isRunning():
            self.fetcher.terminate()
        self.action = None
        self.toolbar = None
        self.tool_button = None
        self.menu = None

    # ------------------------------------------------------------------
    # Core logic
    # ------------------------------------------------------------------

    def _start_fetch(self):
        self.fetcher = CapabilitiesFetcher()
        self.fetcher.finished_ok.connect(self._on_fetch_ok)
        self.fetcher.finished_error.connect(self._on_fetch_error)
        self.fetcher.start()

    def _on_fetch_ok(self, layers):
        def resolution_rank(item):
            title = item[0]
            if "8cm" in title:
                return 0
            if "25cm" in title:
                return 1
            return 2
        self.layers_cache = sorted(layers, key=resolution_rank)

    def _on_fetch_error(self, message):
        self.layers_cache = []
        QMessageBox.warning(
            self.iface.mainWindow(),
            "Quick Dutch Basemap",
            "Could not reach the PDOK WMS service to fetch the "
            f"layer list.\n\nDetails: {message}",
        )

    def _populate_menu(self):
        self.menu.clear()
        if self.layers_cache is None:
            loading_action = self.menu.addAction("Loading layers…")
            loading_action.setEnabled(False)
            return
        if not self.layers_cache:
            empty_action = self.menu.addAction("No layers available")
            empty_action.setEnabled(False)
            return

        current_group = None
        for title, name in self.layers_cache:
            group = "8cm" if "8cm" in title else ("25cm" if "25cm" in title else "other")
            if group != current_group:
                if current_group is not None:
                    self.menu.addSeparator()
                header_text = {"8cm": "8cm layers", "25cm": "25cm layers", "other": "Other"}[group]
                header_action = self.menu.addAction(header_text)
                header_action.setEnabled(False)
                current_group = group

            action = self.menu.addAction(_short_label(title))
            action.triggered.connect(
                lambda checked=False, n=name, t=title: self._load_wms_layer(n, t)
            )

    def _load_wms_layer(self, layer_name, layer_title):
        uri = (
            f"crs={TARGET_CRS}"
            "&format=image/png"
            f"&layers={QUrl.toPercentEncoding(layer_name).data().decode()}"
            "&styles="
            f"&url={QUrl.toPercentEncoding(WMS_BASE_URL).data().decode()}"
        )
        raster_layer = QgsRasterLayer(uri, layer_title, "wms")

        if not raster_layer.isValid():
            QMessageBox.warning(
                self.iface.mainWindow(),
                "Quick Dutch Basemap",
                f'Failed to load layer "{layer_title}". '
                "The PDOK service may be unavailable or the layer name has changed.",
            )
            return

        QgsProject.instance().addMapLayer(raster_layer)
