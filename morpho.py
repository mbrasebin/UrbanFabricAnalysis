from PyQt5.QtGui import QTransform
from qgis.core import QgsField, QgsGeometry, QgsPointXY, QgsRectangle
import math
import numpy
from statistics import *
"""
SMBR computation.
"""
def normalizedAngle(angle):
    clippedAngle = angle
    if ( clippedAngle >= math.pi * 2 or clippedAngle <= -2 * math.pi ):
        clippedAngle = math.fmod( clippedAngle, 2 * math.pi)
    if ( clippedAngle < 0.0 ):
        clippedAngle += 2 * math.pi
    return clippedAngle

def lineAngle(x1, y1, x2, y2):
    at = math.atan2( y2 - y1, x2 - x1 )
    a = -at + math.pi / 2.0
    return normalizedAngle( a )

def compute_SMBR(geom):
    area = float("inf")
    angle = 0
    width = float("inf")
    height =  float("inf")
    if (geom is None):
        return  QgsGeometry()
    hull = geom.convexHull()
    if ( hull.isEmpty() ):
        return QgsGeometry()
    x = hull.asPolygon()
    vertexId = 0
    pt0 = x[0][vertexId]
    pt1 = pt0
    prevAngle = 0.0
    size = len(x[0])
    for vertexId in range(0,  size-0):
        pt2 = x[0][vertexId]
        currentAngle = lineAngle( pt1.x(), pt1.y(), pt2.x(), pt2.y() )
        rotateAngle = 180.0 / math.pi *  (currentAngle - prevAngle)
        prevAngle = currentAngle
        t = QTransform.fromTranslate( pt0.x(), pt0.y() )
        t.rotate(rotateAngle)
        t.translate( -pt0.x(), -pt0.y() )
        hull.transform(t)
        bounds = hull.boundingBox()
        currentArea = bounds.width() * bounds.height()
        if ( currentArea  < area ):
            minRect = bounds
            area = currentArea
            angle = 180.0 / math.pi * currentAngle
            width = bounds.width()
            height = bounds.height()
        pt2 = pt1
    minBounds = QgsGeometry.fromRect( minRect )
    minBounds.rotate( angle, QgsPointXY( pt0.x(), pt0.y() ) )
    if ( angle > 180.0 ):
        angle = math.fmod( angle, 180.0 )
    return minBounds, area, angle, width, height

def m(c,i,g):
    attr = c.attribute(i)
    area = c.geometry().intersection(g).area()
    return (attr,area)

def find_areas(geom, index, dictionary, idAttribute):
    return [m(candidate, idAttribute, geom)
            for candidate in
            map(lambda id:dictionary[id], index.intersects(geom.boundingBox()))
            if candidate.geometry().intersects(geom)]

def find(geom, index, dictionary, idAttribute):
    intersections = find_areas(geom, index, dictionary, idAttribute)
    return max(intersections, key=lambda x: x[1])[0]

def distance_from_polygon_to_layer(geom, index, dictionary, layer_id):
    point = geom.pointOnSurface().asPoint()
    distance = dictionary[index.nearestNeighbor(point,1)[0]].geometry().distance(geom)
    #    print(point.wellKnownText())
    #    print(distance)
    bbox = geom.buffer(distance+1,3).boundingBox()
    #    print(bbox.asWktPolygon())
    return min(
        ((f.geometry().distance(geom), f.attribute(layer_id))
         for f in map(lambda id: dictionary[id], index.intersects(bbox))),
        key=lambda x: x[0])

def compute_elongation(d1, d2):
    """
    Calcul de l'élongation.
    """
    elongation = min(d1,d2)/max(d1,d2)
    return elongation

def compute_compactness(area, perimeter):
    """
    Calcul de la compacité.
    """
    return 4 * math.pi * area / (perimeter * perimeter)

def compute_convexity1(geom, area):
    """
    Calcul de la convexité selon l'enveloppe convexe.
    """
    convexhull = geom.convexHull()
    convexity1 = area/convexhull.area()
    return convexity1

def compute_convexity2(area, SMBR_area):
    """
    Calcul de la convexité selon le SMBR.
    """
    convexity2 = area/SMBR_area	
    return convexity2

def compute_formFactor(hauteur, SMBR_area):
    """
    Calcul du facteur de forme
    """
    formFactor = hauteur * 2 / SMBR_area
    return formFactor

def standard_deviation(l):
    if len(l) > 1: return stdev(l)
    return 0

def deciles(l): return numpy.percentile(l, numpy.arange(0, 100, 10))

def deciles_as_str(l): return numpy.array2string(deciles(l), precision=2, separator=',',suppress_small=True)
