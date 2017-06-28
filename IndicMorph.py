# -*- coding: utf-8 -*-
"""
/***************************************************************************
 IndicateursMorpho
                                 A QGIS plugin
 descr
                              -------------------
        begin                : 2017-05-19
        git sha              : $Format:%H$
        copyright            : (C) 2017 by moi
        email                : abcd@efgh.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant, Qt
from PyQt5.QtGui import QIcon, QTransform
from PyQt5.QtWidgets import QAction, QProgressBar, QMessageBox
# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .IndicMorph_dialog import IndicateursMorphoDialog
import os.path
from qgis.core import QgsVectorLayer, QgsFeature, QgsSpatialIndex, QgsVectorFileWriter, QgsProject
from qgis.core import QgsFeatureRequest, QgsField, QgsGeometry, QgsPoint, QgsRectangle
from .morpho import *


class IndicateursMorpho:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'IndicateursMorpho_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Indicateurs morphologiques')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'IndicateursMorpho')
        self.toolbar.setObjectName(u'IndicateursMorpho')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('IndicateursMorpho', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = IndicateursMorphoDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/IndicateursMorpho/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'IndicateursMorpho'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Indicateurs morphologiques'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar    

    def run(self):
        """Run method that performs all the real work"""

        self.dlg.couche.clear()
        self.dlg.indicateur.clear()
        self.dlg.routes.clear()
        self.dlg.iris.clear()

        #set the couche combobox items
        layers = QgsProject.instance().mapLayers().values()
        for layer in layers:
            self.dlg.couche.addItem(layer.name(),layer)
            self.dlg.routes.addItem(layer.name(),layer)
            self.dlg.vegetation.addItem(layer.name(),layer)
            self.dlg.iris.addItem(layer.name(),layer)

        #set the indicateur combobox items
        self.dlg.indicateur.addItem("elongation")
        self.dlg.indicateur.addItem("aire")
        self.dlg.indicateur.addItem("aire / perimetre")
        self.dlg.indicateur.addItem("distance a la route")
        self.dlg.indicateur.addItem("complexite")
        self.dlg.indicateur.addItem("facteur de forme")
        self.dlg.indicateur.addItem("coefficient d'emprise au sol")
        self.dlg.indicateur.addItem("densite batie")
        self.dlg.indicateur.addItem("densite vegetale")

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        
        # See if OK was pressed
        if result:


            print("Bravo")
            
            #get the index of the combobox
            indexCouche = self.dlg.couche.currentIndex()
            indexIndicateur = self.dlg.indicateur.currentIndex()
            indexRoutes = self.dlg.routes.currentIndex()
            indexVegetation = self.dlg.vegetation.currentIndex()
            indexIRIS = self.dlg.iris.currentIndex()
            layer_bati = self.dlg.couche.itemData(indexCouche)
            layer_routes = self.dlg.routes.itemData(indexRoutes)
            features_road = {RFeature.id(): RFeature for RFeature in layer_routes.getFeatures()}
            layer_vegetation = self.dlg.vegetation.itemData(indexVegetation)
            layer_IRIS = self.dlg.iris.itemData(indexIRIS)

            liste_IRIS = sorted([f.attribute("DCOMIRIS") for f in layer_IRIS.getFeatures()])
#            for f in layer_IRIS.getFeatures():
#                n=f.attribute("DCOMIRIS")
#                liste_IRIS = addListe(liste_IRIS,0,int(n))

            # create layer
            vl = QgsVectorLayer("Polygon", layer_bati.name(), "memory")
            pr = vl.dataProvider()

            # Enter editing mode
            vl.startEditing()

            # add fields
            fields = [
                QgsField("ID", QVariant.Double),
                QgsField("area", QVariant.Double),
                QgsField("SMBR_area", QVariant.Double),
                QgsField("SMBR_angle", QVariant.Double),
                QgsField("SMBR_width", QVariant.Double),
                QgsField("SMBR_height", QVariant.Double),
                QgsField("convexity1", QVariant.Double),    
                QgsField("convexity2", QVariant.Double),
                QgsField("elongation", QVariant.Double),
                QgsField("compactness", QVariant.Double),
                QgsField("area_per_perimeter", QVariant.Double),
                QgsField("IRIS",QVariant.Double),
                QgsField("distToRoad",QVariant.Double),
                QgsField("complexity",QVariant.Double),
                QgsField("formFactor", QVariant.Double),
                QgsField("nearRoad",QVariant.String)]

            #create spatial index

            SIndex_routes = QgsSpatialIndex()
            for feat_route in layer_routes.getFeatures():
                SIndex_routes.insertFeature(feat_route)
            
            # add the new measures to the features
            pr.addAttributes( fields )
            vl.updateFields()

            progressMessageBar = self.iface.messageBar().createMessage("Computing measures...")
            progress = QProgressBar()
            progress.setMaximum(layer_bati.featureCount())
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            self.iface.messageBar().pushWidget(progressMessageBar, self.iface.messageBar().INFO)

            areas = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            elongations = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            featureList = []
            featureListBis = []
            area_perimeters = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            dens_batie = [0 for j in range(len(liste_IRIS))]
            distToRoads = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            dens_vegetale = [0 for j in range(len(liste_IRIS))]
            complexities = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            formFactors = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            i = 0
            
            # add features
            for f in layer_bati.getFeatures():
                geom = f.geometry()
                area = geom.area()
                perimeter = geom.length()
                hauteur = f.attribute("HAUTEUR")
                ident = f.attribute("ID")

                #recherche de l'IRIS du batiment
                iris_id = findIRIS(geom,layer_IRIS,"DCOMIRIS")

                if iris_id != 0:
                    index_iris = findIndex(liste_IRIS,int(iris_id))

                #calcul des indicateurs a l'echelle du batiment


                roadList = []
                dist = 0
                while roadList == [] and dist < 20000:
                    dist += 300
                    zone = geom.buffer(dist,10).boundingBox()
                    roadList = SIndex_routes.intersects(zone)
                distToRoadMin = -1
                for f_road_id in roadList:
                    f_road = features_road[f_road_id]
                    distToRoad = f_road.geometry().distance(geom)
                    if distToRoadMin == -1:
                        distToRoadMin = distToRoad
                        nRoad = f_road.attribute("ID")
                    elif(distToRoad<distToRoadMin):
                        distToRoadMin = distToRoad
                        nRoad = f_road.attribute("ID")
                
                """
                nearestRoad = SIndex_routes.nearestNeighbor(geom.centroid().asPoint(),1)
                for road in layer_routes.getFeatures():
                    if road.id() == nearestRoad[0]:
                        nRoad = road
                distToRoadMin = nRoad.geometry().distance(geom)
                """

                """
                distToRoadMin = -1
                for f_road in layer_routes.getFeatures():
                    distToRoad = f_road.geometry().distance(geom)
                    if distToRoadMin == -1:
                        distToRoadMin = distToRoad
                    else:
                        distToRoadMin = min(distToRoad,distToRoadMin)
                """
                        
                param_SMBR = compute_SMBR(geom)
                SMBR_geom = param_SMBR[0]
                SMBR_area = param_SMBR[1]
                SMBR_angle = param_SMBR[2]
                SMBR_width = param_SMBR[3]
                SMBR_height = param_SMBR[4]
                convexity1 = compute_convexity1(geom, area)
                convexity2 = compute_convexity2(area, SMBR_area)
                elongation = compute_elongation(SMBR_height, SMBR_width)
                compactness = compute_compactness(area, perimeter)
                complexity = len(geom.asPolygon()[0])
                formFactor = compute_formFactor(hauteur, SMBR_area)
                #remplissage des listes pour les calculs a l'echelle de l'IRIS
                if iris_id != 0:
                    elongations[index_iris][1] += [elongation]
                    area_perimeters[index_iris][1] += [area/perimeter]
                    areas[index_iris][1] += [area]
                    dens_batie[index_iris] += area*(hauteur*5/2)
                    if distToRoadMin >= 0:
                        distToRoads[index_iris][1] += [distToRoadMin]
                    complexities[index_iris][1] += [complexity]
                    formFactors[index_iris][1] += [formFactor]

                feat = QgsFeature()
                feat.setGeometry( geom )
                feat.initAttributes(len(fields))
                feat.setAttribute( 0, ident)
                feat.setAttribute( 1, area )
                feat.setAttribute( 2, SMBR_area )
                feat.setAttribute( 3, SMBR_angle )
                feat.setAttribute( 4, SMBR_width )
                feat.setAttribute( 5, SMBR_height )
                feat.setAttribute( 6, convexity1 )
                feat.setAttribute( 7, convexity2 )
                feat.setAttribute( 8, elongation)
                feat.setAttribute( 9, compactness )
                feat.setAttribute( 10, area/perimeter)
                feat.setAttribute( 11, iris_id)
                if distToRoadMin >= 0:
                    feat.setAttribute( 12, distToRoadMin)
                feat.setAttribute( 13, complexity)
                feat.setAttribute( 14, formFactor)
                feat.setAttribute(15, nRoad)
                featureList.append(feat)
                i += 1
                progress.setValue(i)

            pr.addFeatures (featureList)
            vl.commitChanges()

            for fVeget in layer_vegetation.getFeatures():
                geomV = fVeget.geometry()
                areaV = geomV.area()
                iris_areasV = findIRIS_areas(geomV,layer_IRIS,"DCOMIRIS")
                for element in iris_areasV:
                    index_irisV = findIndex(liste_IRIS,int(element[0]))
                    dens_vegetale[index_irisV] += element[1]

            # create layer iris
            irisBis = QgsVectorLayer("Polygon", layer_IRIS.name(), "memory")
            prBis = irisBis.dataProvider()

            # Enter editing mode
            irisBis.startEditing()

            # add fields
            fieldsBis = [
                QgsField("id", QVariant.Double),
                QgsField("nb_batis", QVariant.Double),
                QgsField("area_med", QVariant.Double),
                QgsField("area_moy", QVariant.Double),
                QgsField("area_ect", QVariant.Double),
                QgsField("area_dec", QVariant.Double),
                QgsField("elong_med", QVariant.Double),
                QgsField("elong_moy", QVariant.Double),
                QgsField("elong_ect", QVariant.Double),
                QgsField("elong_dec", QVariant.Double),
                QgsField("areaper_med", QVariant.Double),
                QgsField("areaper_moy", QVariant.Double),
                QgsField("areaper_ect", QVariant.Double),
                QgsField("areaper_dec", QVariant.Double),
                QgsField("ces",QVariant.Double),
                QgsField("dens_batie", QVariant.Double),
                QgsField("dsRoad_med",QVariant.Double),
                QgsField("dsRoad_moy",QVariant.Double),
                QgsField("dsRoad_ect",QVariant.Double),
                QgsField("dsRoad_dec",QVariant.Double),
                QgsField("dens_veget",QVariant.Double),
                QgsField("compl_med",QVariant.Double),
                QgsField("compl_moy",QVariant.Double),
                QgsField("compl_ect",QVariant.Double),
                QgsField("compl_dec",QVariant.Double),
                QgsField("formF_med",QVariant.Double),
                QgsField("formF_moy",QVariant.Double),
                QgsField("formF_ect",QVariant.Double),
                QgsField("formF_dec",QVariant.Double)
                ]
            
            # add the new measures to the features
            prBis.addAttributes( fieldsBis )
            irisBis.updateFields()


            for featIRIS in layer_IRIS.getFeatures():
                geomI = featIRIS.geometry()
                areaI = geomI.area()
                ID = featIRIS.attribute("ID")
                indexI = findIndex(liste_IRIS,int(ID))
                areasI = areas[indexI][1]
                elongationsI = elongations[indexI][1]
                area_perimetersI = area_perimeters[indexI][1]
                nb_batiments = len(areas[indexI][1])
                sum_areas = sum(areasI)
                distToRoadsI = distToRoads[indexI][1]
                dens_vegetaleI = dens_vegetale[indexI]
                complexitiesI = complexities[indexI][1]
                formFactorsI = formFactors[indexI][1]

                if nb_batiments > 0:
                    print(ID)
                    print("Area")
                    print(deciles(areasI))
                    print("Elongation")
                    print(deciles(elongationsI))
                    print("Area / perimeter")
                    print(deciles(area_perimetersI))
                    print("Distance to road")
                    print(deciles(distToRoadsI))
                    print("Complexity")
                    print(deciles(complexitiesI))
                    print("Form factor")
                    print(deciles(formFactorsI))

            
                feat = QgsFeature()
                feat.setGeometry( geomI )
                feat.initAttributes(len(fieldsBis))
                feat.setAttribute( 0, ID )
                feat.setAttribute( 1, nb_batiments )
                if nb_batiments > 0:
                    feat.setAttribute( 2, median(areasI) )
                    feat.setAttribute( 3, mean(areasI) )
                    feat.setAttribute( 4, standard_deviation(areasI) )
                    #feat.setAttribute( 5, deciles(areasI) )
                    feat.setAttribute( 6, median(elongationsI) )
                    feat.setAttribute( 7, mean(elongationsI) )
                    feat.setAttribute( 8, standard_deviation(elongationsI))
                    #feat.setAttribute( 9, deciles(elongationsI) )
                    feat.setAttribute( 10, median(area_perimetersI))
                    feat.setAttribute( 11, mean(area_perimetersI))
                    feat.setAttribute( 12, standard_deviation(area_perimetersI))
                    #feat.setAttribute( 13, deciles(area_perimetersI))
                    feat.setAttribute( 14, sum_areas / areaI)
                    feat.setAttribute( 15, dens_batie[indexI]/areaI)
                    feat.setAttribute( 16, median(distToRoadsI))
                    feat.setAttribute( 17, mean(distToRoadsI))
                    feat.setAttribute( 18, standard_deviation(distToRoadsI))
                    #feat.setAttribute( 19, deciles(distToRoadsI))
                    feat.setAttribute( 20, dens_vegetaleI / areaI)
                    feat.setAttribute( 21, median(complexitiesI))
                    feat.setAttribute( 22, mean(complexitiesI))
                    feat.setAttribute( 23, standard_deviation(complexitiesI))
                    #feat.setAttribute( 24, deciles(complexitiesI))
                    feat.setAttribute( 25, median(formFactorsI))
                    feat.setAttribute( 26, mean(formFactorsI))
                    feat.setAttribute( 27, standard_deviation(formFactorsI))
                    #feat.setAttribute( 28, deciles(formFactorsI))
                    

                featureListBis.append(feat)

            

            prBis.addFeatures( featureListBis ) 
            irisBis.commitChanges()


            #Calcul de l'indicateur demande uniquement
            
            """ind = ""
            res=[]
            if indexIndicateur == 0:
                res = [elongation_moy,elongation_med,elongation_ect,elongation_dec]
                ind = "elongation (average, median, standard deviation, deciles)"

            elif indexIndicateur == 1:
                res = [area_moy,area_med,area_ect,area_dec]
                ind = "area (average, median, standard deviation, deciles)"

            elif indexIndicateur == 2:
                res = [area_peri_moy,area_peri_med,area_peri_ect,area_peri_dec]
                ind = "area / perimeter (average, median, standard deviation, deciles)"

            elif indexIndicateur == 3:
                res = []
                for f in layer_bati.getFeatures():
                    geom = f.geometry()
                    smbr = compute_SMBR(geom)
                    res.append(compute_convexity2(geom.area(),smbr[1]))
                    i = i + 1
                    progress.setValue(i)
                ind = "convexity depending on SMBR" """
                

            QgsProject.instance().addMapLayer(vl)
            QgsProject.instance().addMapLayer(irisBis)
            #QMessageBox.information(self.iface.mainWindow(),ind,str(res))

            self.iface.messageBar().clearWidgets()

