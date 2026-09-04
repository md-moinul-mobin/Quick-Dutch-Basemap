# -*- coding: utf-8 -*-
"""
Quick Dutch Basemap
--------------------
A QGIS plugin that instantly loads PDOK Dutch aerial photo (luchtfoto)
WMS basemaps into the current project.

Author: MD Moinul Mobin
"""


def classFactory(iface):
    """Load QuickDutchBasemap class from file quick_dutch_basemap.py.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .quick_dutch_basemap import QuickDutchBasemap
    return QuickDutchBasemap(iface)
