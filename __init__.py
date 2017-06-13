# -*- coding: utf-8 -*-
"""
/***************************************************************************
 IndicateursMorpho
                                 A QGIS plugin
 descr
                             -------------------
        begin                : 2017-05-19
        copyright            : (C) 2017 by moi
        email                : abcd@efgh.fr
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load IndicateursMorpho class from file IndicateursMorpho.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .IndicMorph import IndicateursMorpho
    return IndicateursMorpho(iface)
