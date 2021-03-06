# -*- coding: utf-8 -*-

"""
***************************************************************************
    DensifyGeometriesInterval.py by Anita Graser, Dec 2012
      based on
    DensifyGeometries.py
    ---------------------
    Date                 : October 2012
    Copyright            : (C) 2012 by Victor Olaya
    Email                : volayaf at gmail dot com
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

__author__ = 'Anita Graser'
__date__ = 'Dec 2012'
__copyright__ = '(C) 2012, Anita Graser'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

from math import sqrt

from PyQt4.QtCore import *

from qgis.core import *

from sextante.core.GeoAlgorithm import GeoAlgorithm
from sextante.core.QGisLayers import QGisLayers

from sextante.parameters.ParameterVector import ParameterVector
from sextante.parameters.ParameterNumber import ParameterNumber
from sextante.parameters.ParameterBoolean import ParameterBoolean

from sextante.outputs.OutputVector import OutputVector

class DensifyGeometriesInterval(GeoAlgorithm):

    INPUT = "INPUT"
    #VERTICES = "VERTICES"
    INTERVAL = "INTERVAL"
    USE_SELECTION = "USE_SELECTION"
    OUTPUT = "OUTPUT"

    #def getIcon(self):
    #    return QtGui.QIcon(os.path.dirname(__file__) + "/icons/de.png")

    def defineCharacteristics(self):
        self.name = "Densify geometries given an interval"
        self.group = "Geometry tools"

        self.addParameter(ParameterVector(self.INPUT, "Input layer", ParameterVector.VECTOR_TYPE_ANY))
        #self.addParameter(ParameterNumber(self.VERTICES, "Vertices to add", 1, 10000000, 1))
        self.addParameter(ParameterNumber(self.INTERVAL, "Interval between Vertices to add", 1, 10000000, 1))
        self.addParameter(ParameterBoolean(self.USE_SELECTION, "Use only selected features", False))

        self.addOutput(OutputVector(self.OUTPUT, "Simplified layer"))

    def processAlgorithm(self, progress):
        layer = QGisLayers.getObjectFromUri(self.getParameterValue(self.INPUT))
        useSelection = self.getParameterValue(self.USE_SELECTION)
        #vertices =self.getParameterValue(self.VERTICES)
        interval =self.getParameterValue(self.INTERVAL)

        isPolygon = layer.geometryType() == QGis.Polygon

        provider = layer.dataProvider()
        layer.select(layer.pendingAllAttributesList())

        writer = self.getOutputFromName(self.OUTPUT).getVectorWriter(layer.pendingFields(),
                     layer.wkbType(), provider.crs())

        current = 0
        if useSelection:
            selection = layer.selectedFeatures()
            total = 100.0 / float(len(selection))
            for f in selection:
                featGeometry = QgsGeometry(f.geometry())
                attrMap = f.attributeMap()
                #newGeometry = self.densifyGeometry(featGeometry, int(vertices), isPolygon)
                newGeometry = self.densifyGeometry(featGeometry, interval, isPolygon)

                feature = QgsFeature()
                feature.setGeometry(newGeometry)
                feature.setAttributeMap(attrMap)
                writer.addFeature(feature)

                current += 1
                progress.setPercentage(int(current * total))
        else:
            total = 100.0 / float(provider.featureCount())
            f = QgsFeature()
            while layer.nextFeature(f):
                featGeometry = QgsGeometry(f.geometry())
                attrMap = f.attributeMap()
                #newGeometry = self.densifyGeometry(featGeometry, int(vertices), isPolygon)
                newGeometry = self.densifyGeometry(featGeometry, interval, isPolygon)

                feature = QgsFeature()
                feature.setGeometry(newGeometry)
                feature.setAttributeMap(attrMap)
                writer.addFeature(feature)

                current += 1
                progress.setPercentage(int(current * total))

        del writer

    #def densifyGeometry(self, geometry, pointsNumber, isPolygon):
    def densifyGeometry(self, geometry, interval, isPolygon):
        output = []
        if isPolygon:
            if geometry.isMultipart():
                polygons = geometry.asMultiPolygon()
                for poly in polygons:
                    p = []
                    for ring in poly:
                        #p.append(self.densify(ring, pointsNumber))
                        p.append(self.densify(ring, interval))
                    output.append(p)
                return QgsGeometry.fromMultiPolygon(output)
            else:
                rings = geometry.asPolygon()
                for ring in rings:
                    #output.append(self.densify(ring, pointsNumber))
                    output.append(self.densify(ring, interval))
                return QgsGeometry.fromPolygon(output)
        else:
            if geometry.isMultipart():
                lines = geometry.asMultiPolyline()
                for points in lines:
                    #output.append(self.densify(points, pointsNumber))
                    output.append(self.densify(points, interval))
                return QgsGeometry.fromMultiPolyline(output)
            else:
                points = geometry.asPolyline()
                #output = self.densify(points, pointsNumber)
                output = self.densify(points, interval)
                return QgsGeometry.fromPolyline(output)

    #def densify(self, polyline, pointsNumber):
    def densify(self, polyline, interval):
        output = []
        for i in xrange(len(polyline) - 1):
            p1 = polyline[i]
            p2 = polyline[i + 1]
            output.append(p1)
            # calculate necessary number of points between p1 and p2
            pointsNumber = sqrt(p1.sqrDist(p2)) / interval 
            if pointsNumber > 1:
                multiplier = 1.0 / float(pointsNumber)
            else:
                multiplier = 1
            for j in xrange(int(pointsNumber)):
                delta = multiplier * (j + 1)
                x = p1.x() + delta * (p2.x() - p1.x())
                y = p1.y() + delta * (p2.y() - p1.y())
                output.append(QgsPoint( x, y ))
                if j + 1 == pointsNumber:
                    break
        output.append(polyline[len(polyline) - 1])
        return output
