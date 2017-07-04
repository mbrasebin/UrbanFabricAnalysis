import sys
import os
from qgis.core import *
from PyQt5.QtCore import QVariant
from morpho import *
from statistics import *

input_dir = sys.argv[1]
output_dir = sys.argv[2]
os.makedirs(output_dir)

# supply path to qgis install location
QgsApplication.setPrefixPath("/usr", True)

# create a reference to the QgsApplication, setting the second argument to False disables the GUI
qgs = QgsApplication([], False)

# load providers
qgs.initQgis()

# Write your code here to load some layers, use processing algorithms, etc.
layer_buildings = QgsVectorLayer(input_dir+'/buildings.shp', 'layer_buildings', 'ogr')
layer_roads = QgsVectorLayer(input_dir+'/roads.shp', 'layer_roads', 'ogr')
layer_vegetation = QgsVectorLayer(input_dir+'/vegetation.shp', 'layer', 'ogr')
layer_aggregation = QgsVectorLayer(input_dir+'/aggregation.shp', 'layer_aggregation', 'ogr')

building_height_name = "HAUTEUR"
building_id_name = "ID"
aggregation_id_name = "DCOMIRIS"
road_id = "ID"

# add fields
fields = QgsFields()
fields.append(QgsField("ID", QVariant.String))
fields.append(QgsField("area", QVariant.Double))
fields.append(QgsField("volume", QVariant.Double))
fields.append(QgsField("SMBR_area", QVariant.Double))
fields.append(QgsField("SMBR_angle", QVariant.Double))
fields.append(QgsField("SMBR_width", QVariant.Double))
fields.append(QgsField("SMBR_height", QVariant.Double))
fields.append(QgsField("convexity1", QVariant.Double))
fields.append(QgsField("convexity2", QVariant.Double))
fields.append(QgsField("elongation", QVariant.Double))
fields.append(QgsField("compactness", QVariant.Double))
fields.append(QgsField("area_per_perimeter", QVariant.Double))
fields.append(QgsField("IRIS",QVariant.String))
fields.append(QgsField("distToRoad",QVariant.Double))
fields.append(QgsField("complexity",QVariant.Double))
fields.append(QgsField("formFactor", QVariant.Double))
fields.append(QgsField("nearRoad",QVariant.String))
fields.append(QgsField("SMBR_angle_90", QVariant.Double))

buildings_writer = QgsVectorFileWriter(output_dir+"/buildings_out.shp", "utf-8", fields,
                             QgsWkbTypes.Polygon, layer_buildings.sourceCrs(),
                             "ESRI Shapefile")

#create spatial indexes
road_index = QgsSpatialIndex()
for f in layer_roads.getFeatures(): road_index.insertFeature(f)
building_index = QgsSpatialIndex()
for f in layer_buildings.getFeatures(): building_index.insertFeature(f)
aggregation_index = QgsSpatialIndex()
for f in layer_aggregation.getFeatures(): aggregation_index.insertFeature(f)

# Create dictionaries of all features
aggregation_dict = {f.id(): f for f in layer_aggregation.getFeatures()}
road_dict = {f.id(): f for f in layer_roads.getFeatures()}
area_dict = {f.attribute(aggregation_id_name): [] for f in layer_aggregation.getFeatures()}
elongation_dict = {f.attribute(aggregation_id_name): [] for f in layer_aggregation.getFeatures()}
area_perimeter_dict = {f.attribute(aggregation_id_name): [] for f in layer_aggregation.getFeatures()}
volume_dict = {f.attribute(aggregation_id_name): [] for f in layer_aggregation.getFeatures()}
density_dict = {f.attribute(aggregation_id_name): [] for f in layer_aggregation.getFeatures()}
distance_dict = {f.attribute(aggregation_id_name): [] for f in layer_aggregation.getFeatures()}
complexity_dict = {f.attribute(aggregation_id_name): [] for f in layer_aggregation.getFeatures()}
form_dict = {f.attribute(aggregation_id_name): [] for f in layer_aggregation.getFeatures()}
veg_density_dict = {f.attribute(aggregation_id_name): [] for f in layer_aggregation.getFeatures()}

for f in layer_vegetation.getFeatures():
    geom_v = f.geometry()
    agg_areas = find_areas(geom_v,aggregation_index,aggregation_dict,aggregation_id_name)
    for elem in agg_areas:
        veg_density_dict[elem[0]].append(elem[1])

# loop through building layer
i = 0
for elem in layer_buildings.getFeatures():
    geom = elem.geometry()
    area = geom.area()
    perimeter = geom.length()
    height = elem.attribute(building_height_name)
    ident = elem.attribute(building_id_name)
    #    print(ident)
    #recherche de l'aggregation à laquelle appartient le batiment
    aggregation_id = find(geom,aggregation_index,aggregation_dict,aggregation_id_name)
    #calcul des indicateurs a l'echelle du batiment
    distToRoadMin, road = distance_from_polygon_to_layer(geom, road_index, road_dict, road_id)
    ombb_geometry, ombb_area, ombb_angle, ombb_width, ombb_height = geom.orientedMinimumBoundingBox()
    convexity1 = compute_convexity1(geom, area)
    convexity2 = compute_convexity2(area, ombb_area)
    elongation = compute_elongation(ombb_height, ombb_width)
    compactness = compute_compactness(area, perimeter)
    complexity = len(geom.asPolygon()[0]) - 1
    formFactor = compute_formFactor(height, ombb_area)
    #remplissage des listes pour les calculs a l'echelle de l'IRIS
    #aggregation_building_dict[aggregation_id].append(elem.id())
    elongation_dict[aggregation_id].append(elongation)
    area_perimeter_dict[aggregation_id].append(area/perimeter)
    area_dict[aggregation_id].append(area)
    volume_dict[aggregation_id].append(area * height)
    density_dict[aggregation_id].append(area*(height*5/2))
    distance_dict[aggregation_id].append(distToRoadMin)
    complexity_dict[aggregation_id].append(complexity)
    form_dict[aggregation_id].append(formFactor)

    feat = QgsFeature()
    feat.setGeometry( geom )
    feat.initAttributes(len(fields))
    feat.setAttribute( 0, ident)
    feat.setAttribute( 1, area )
    feat.setAttribute( 2, area * height)
    feat.setAttribute( 3, ombb_area )
    feat.setAttribute( 4, ombb_angle )
    feat.setAttribute( 5, ombb_width )
    feat.setAttribute( 6, ombb_height )
    feat.setAttribute( 7, convexity1 )
    feat.setAttribute( 8, convexity2 )
    feat.setAttribute( 9, elongation)
    feat.setAttribute( 10, compactness )
    feat.setAttribute( 11, area/perimeter)
    feat.setAttribute( 12, aggregation_id)
    if distToRoadMin >= 0:
        feat.setAttribute( 13, distToRoadMin)
    feat.setAttribute( 14, complexity)
    feat.setAttribute( 15, formFactor)
    feat.setAttribute( 16, road)
    feat.setAttribute( 17, ombb_angle % 90)
    #featureList.append(feat)
    buildings_writer.addFeature(feat)
    i = i+1
    if (i%1000 == 0): print(i)

del buildings_writer

aggregation_fields = QgsFields()
aggregation_fields.append(QgsField("id", QVariant.String))
aggregation_fields.append(QgsField("nb_batis", QVariant.Double))
aggregation_fields.append(QgsField("area_med", QVariant.Double))
aggregation_fields.append(QgsField("area_moy", QVariant.Double))
aggregation_fields.append(QgsField("area_ect", QVariant.Double))
aggregation_fields.append(QgsField("area_dec", QVariant.String))
aggregation_fields.append(QgsField("volume_med",QVariant.Double))
aggregation_fields.append(QgsField("volume_moy",QVariant.Double))
aggregation_fields.append(QgsField("volume_ect",QVariant.Double))
aggregation_fields.append(QgsField("elong_med", QVariant.Double))
aggregation_fields.append(QgsField("elong_moy", QVariant.Double))
aggregation_fields.append(QgsField("elong_ect", QVariant.Double))
aggregation_fields.append(QgsField("elong_dec", QVariant.String))
aggregation_fields.append(QgsField("areaper_med", QVariant.Double))
aggregation_fields.append(QgsField("areaper_moy", QVariant.Double))
aggregation_fields.append(QgsField("areaper_ect", QVariant.Double))
aggregation_fields.append(QgsField("areaper_dec", QVariant.String))
aggregation_fields.append(QgsField("ces",QVariant.Double))
aggregation_fields.append(QgsField("dens_batie", QVariant.Double))
aggregation_fields.append(QgsField("dsRoad_med",QVariant.Double))
aggregation_fields.append(QgsField("dsRoad_moy",QVariant.Double))
aggregation_fields.append(QgsField("dsRoad_ect",QVariant.Double))
aggregation_fields.append(QgsField("dsRoad_dec",QVariant.String))
aggregation_fields.append(QgsField("dens_veget",QVariant.Double))
aggregation_fields.append(QgsField("compl_med",QVariant.Double))
aggregation_fields.append(QgsField("compl_moy",QVariant.Double))
aggregation_fields.append(QgsField("compl_ect",QVariant.Double))
aggregation_fields.append(QgsField("compl_dec",QVariant.String))
aggregation_fields.append(QgsField("formF_med",QVariant.Double))
aggregation_fields.append(QgsField("formF_moy",QVariant.Double))
aggregation_fields.append(QgsField("formF_ect",QVariant.Double))
aggregation_fields.append(QgsField("formF_dec",QVariant.String))

aggregation_writer = QgsVectorFileWriter(output_dir+"/aggregation_out.shp", "utf-8", aggregation_fields, QgsWkbTypes.Polygon, layer_aggregation.sourceCrs(), "ESRI Shapefile")

for featIRIS in layer_aggregation.getFeatures():
    geomI = featIRIS.geometry()
    areaI = geomI.area()
    ID = featIRIS.attribute(aggregation_id_name)
    areasI = area_dict[ID]
    volumesI = volume_dict[ID]
    elongationsI = elongation_dict[ID]
    area_perimetersI = area_perimeter_dict[ID]
    nb_batiments = len(areasI)
    sum_areas = sum(areasI)
    distToRoadsI = distance_dict[ID]
    densityI = density_dict[ID]
    dens_vegetaleI = veg_density_dict[ID]
    complexitiesI = complexity_dict[ID]
    formFactorsI = form_dict[ID]

    feat = QgsFeature()
    feat.setGeometry( geomI )
    feat.initAttributes(len(aggregation_fields))
    feat.setAttribute( 0, ID )
    feat.setAttribute( 1, nb_batiments )
    if nb_batiments > 0:
        feat.setAttribute( 2, median(areasI) )
        feat.setAttribute( 3, mean(areasI) )
        feat.setAttribute( 4, standard_deviation(areasI) )
        feat.setAttribute( 5, deciles_as_str(areasI) )
        feat.setAttribute( 6, median(volumesI))
        feat.setAttribute( 7, mean(volumesI))
        feat.setAttribute( 8, standard_deviation(volumesI))
        feat.setAttribute( 9, median(elongationsI) )
        feat.setAttribute( 10, mean(elongationsI) )
        feat.setAttribute( 11, standard_deviation(elongationsI))
        feat.setAttribute( 12, deciles_as_str(elongationsI) )
        feat.setAttribute( 13, median(area_perimetersI))
        feat.setAttribute( 14, mean(area_perimetersI))
        feat.setAttribute( 15, standard_deviation(area_perimetersI))
        feat.setAttribute( 16, deciles_as_str(area_perimetersI))
        feat.setAttribute( 17, sum_areas / areaI)
        feat.setAttribute( 18, sum(densityI)/areaI)
        feat.setAttribute( 19, median(distToRoadsI))
        feat.setAttribute( 20, mean(distToRoadsI))
        feat.setAttribute( 21, standard_deviation(distToRoadsI))
        feat.setAttribute( 22, deciles_as_str(distToRoadsI))
        feat.setAttribute( 23, sum(dens_vegetaleI) / areaI)
        feat.setAttribute( 24, median(complexitiesI))
        feat.setAttribute( 25, mean(complexitiesI))
        feat.setAttribute( 26, standard_deviation(complexitiesI))
        feat.setAttribute( 27, deciles_as_str(complexitiesI))
        feat.setAttribute( 28, median(formFactorsI))
        feat.setAttribute( 29, mean(formFactorsI))
        feat.setAttribute( 30, standard_deviation(formFactorsI))
        feat.setAttribute( 31, deciles_as_str(formFactorsI))
    aggregation_writer.addFeature(feat)

del aggregation_writer
print("done")
qgs.exitQgis()
print("done again")
