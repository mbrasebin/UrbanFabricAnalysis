from qgis.core import *

# supply path to qgis install location
QgsApplication.setPrefixPath("/usr", True)

# create a reference to the QgsApplication, setting the
# second argument to False disables the GUI
qgs = QgsApplication([], False)

# load providers
qgs.initQgis()

# Write your code here to load some layers, use processing algorithms, etc.
layer = QgsVectorLayer('/tmp/input.shp', 'layer', 'ogr')
print(layer.isValid())
# loop through layer 
for elem in layer.getFeatures():
    geom = elem.geometry()
    length = geom.length()
    print(length)
    
print("done")
# When your script is complete, call exitQgis() to remove the provider and
# layer registries from memory
qgs.exitQgis()
print("done again")
