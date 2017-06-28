from PyQt5.QtGui import QTransform
from qgis.core import QgsField, QgsGeometry, QgsPointXY, QgsRectangle
import math
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

def addListe(l, i, n):
    if i == len(l):
        return l + [n]
    elif n < l[i] :
        return l[0:i]+[n]+l[i:len(l)]
    elif n > l[i] :
        return addListe(l, i+1, n)
    else:
        return l

def findIndex(l, n):
    i = 0
    j = len(l)-1
    while i <= j :
        k = int(l[int((i+j)/2)])
        if k == n:
            return int((i+j)/2)
        elif k > n:
            j = int((j+i)/2-1)
        else :
            i = int((j+i)/2+1)
    if i > j:
        return 0

def findIRIS_areas(geom, layer_IRIS, idAttribute):
    intersections = []
    for iris in layer_IRIS.getFeatures():
        if iris.geometry().intersects(geom):
            intersections.append([iris.attribute(idAttribute),iris.geometry().intersection(geom).area()])
    return intersections

def findIRIS(geom, layer_IRIS, idAttribute):
    intersections = findIRIS_areas(geom, layer_IRIS, idAttribute)
    iris_id = 0
    aire_max = 0
    for element in intersections:
        if element[1] > aire_max:
            iris_id = element[0]
            aire_max = element[1]
    return iris_id

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

def mean(l):
    if l == []:
        return "-"
    m = 0.0
    for i in l:
        m += i
    m = m/len(l)
    return m

def variance(l):
    if l == []:
        return "-"
    m = median(l)
    s = 0.0
    for i in l:
        s += i*i
    return s/len(l)-m*m

def standard_deviation(l):
    if l == []:
        return "-"
    return math.sqrt(variance(l))

def median(l):
    if l == []:
        return "-"
    n = len(l)
    t = sorted(l)
    return t[n/2]

def deciles(l):
    if l == []:
        return "-"
    n = len(l)
    t = sorted(l)
    dec = [0 for i in range(9)]
    for i in range(1,10):
        dec[i-1]=t[i*n/10]
    return dec
