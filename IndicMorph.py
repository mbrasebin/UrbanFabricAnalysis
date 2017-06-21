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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant, Qt
from PyQt4.QtGui import QAction, QIcon, QProgressBar, QMessageBox, QTransform
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from IndicMorph_dialog import IndicateursMorphoDialog
import os.path
import math
from qgis.core import QgsVectorLayer, QgsFeature, QgsSpatialIndex, QgsVectorFileWriter, QgsMapLayerRegistry
from qgis.core import QgsFeatureRequest, QgsField, QgsGeometry, QgsPoint, QgsRectangle



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


    """
    Méthode de calcul du SMBR.
    """

    def normalizedAngle(self,  angle):
        clippedAngle = angle
        if ( clippedAngle >= math.pi * 2 or clippedAngle <= -2 * math.pi ):
            clippedAngle = math.fmod( clippedAngle, 2 * math.pi)
        if ( clippedAngle < 0.0 ):
            clippedAngle += 2 * math.pi
        return clippedAngle

    def lineAngle(self, x1, y1, x2, y2):
        at = math.atan2( y2 - y1, x2 - x1 )
        a = -at + math.pi / 2.0
        return self.normalizedAngle( a )

    def compute_SMBR(self, geom):
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
            currentAngle = self.lineAngle( pt1.x(), pt1.y(), pt2.x(), pt2.y() )
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
        minBounds.rotate( angle, QgsPoint( pt0.x(), pt0.y() ) )
        if ( angle > 180.0 ):
            angle = math.fmod( angle, 180.0 )
        return minBounds, area, angle, width, height

    def addListe(self, l, i, n):
        if i == len(l):
            return l + [n]
        elif n < l[i] :
            return l[0:i]+[n]+l[i:len(l)]
        elif n > l[i] :
            return self.addListe(l,i+1,n)
        else:
            return l

    def findIndex(self,l,n):
        i = 0
        j = len(l)-1
        while i <= j :
            k = l[(i+j)/2]
            if k == n:
                return (i+j)/2
            elif k > n:
                j = (j+i)/2-1
            else :
                i = (j+i)/2+1
        if i>j:
            return 0

    def findIRIS_areas(self,liste_IRIS,geom,layer_IRIS):
        intersections = []
        for iris in layer_IRIS.getFeatures():
            if iris.geometry().intersects(geom):
                intersections.append([iris.attribute("ID"),iris.geometry().intersection(geom).area()])
        return intersections

    def findIRIS(self,liste_IRIS,geom,layer_IRIS):
        intersections = self.findIRIS_areas(liste_IRIS,geom,layer_IRIS)
        iris_id = 0
        aire_max = 0
        for element in intersections:
            if element[1]>aire_max:
                iris_id = element[0]
                aire_max = element[1]
        return iris_id

    def compute_elongation(self, d1, d2):
        """
        Calcul de l'élongation.
        """
        elongation = min(d1,d2)/max(d1,d2)
        return elongation

    def compute_compactness(self, area, perimeter):
        """
        Calcul de la compacité.
        """
        return 4 * math.pi * area / (perimeter * perimeter)
    
    def compute_convexity1(self, geom, area):
        """
        Calcul de la convexité selon l'enveloppe convexe.
        """
        convexhull = geom.convexHull()
        convexity1 = area/convexhull.area()
        return convexity1
        
    def compute_convexity2(self, area, SMBR_area):
        """
        Calcul de la convexité selon le SMBR.
        """
        convexity2 = area/SMBR_area	
        return convexity2

    def compute_formFactor(self, hauteur, SMBR_area):
        """
        Calcul du facteur de forme
        """
        formFactor = hauteur * 2 / SMBR_area
        return formFactor

    def moyenne(self, l):
        if l == []:
            return "-"
        m = 0.0
        for i in l:
            m += i
        m = m/len(l)
        return m

    def variance(self, l):
        if l == []:
            return "-"
        m = self.moyenne(l)
        s = 0.0
        for i in l:
            s += i*i
        return s/len(l)-m*m

    def ecart_type(self, l):
        if l == []:
            return "-"
        return math.sqrt(self.variance(l))

    def mediane(self,l):
        if l == []:
            return "-"
        n = len(l)
        t = sorted(l)
        return t[n/2]

    def deciles(self,l):
        if l == []:
            return "-"
        n = len(l)
        t = sorted(l)
        dec = [0 for i in range(9)]
        for i in range(1,10):
            dec[i-1]=t[i*n/10]
        return dec
    

    def run(self):
        """Run method that performs all the real work"""

        self.dlg.couche.clear()
        self.dlg.indicateur.clear()
        self.dlg.routes.clear()
        self.dlg.iris.clear()

        #set the couche combobox items
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
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

            liste_IRIS = []
            for f in layer_IRIS.getFeatures():
                n=f.attribute("ID")
                liste_IRIS = self.addListe(liste_IRIS,0,int(n))
                


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
                iris_id = self.findIRIS(liste_IRIS,geom,layer_IRIS)

                if iris_id != 0:
                    index_iris = self.findIndex(liste_IRIS,int(iris_id))

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
                        
                param_SMBR = self.compute_SMBR(geom)
                SMBR_geom = param_SMBR[0]
                SMBR_area = param_SMBR[1]
                SMBR_angle = param_SMBR[2]
                SMBR_width = param_SMBR[3]
                SMBR_height = param_SMBR[4]
                convexity1 = self.compute_convexity1(geom, area)
                convexity2 = self.compute_convexity2(area, SMBR_area)
                elongation = self.compute_elongation(SMBR_height, SMBR_width)
                compactness = self.compute_compactness(area, perimeter)
                complexity = len(geom.asPolygon()[0])
                formFactor = self.compute_formFactor(hauteur, SMBR_area)
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
                iris_areasV = self.findIRIS_areas(liste_IRIS,geomV,layer_IRIS)
                for element in iris_areasV:
                    index_irisV = self.findIndex(liste_IRIS,int(element[0]))
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
                indexI = self.findIndex(liste_IRIS,int(ID))
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
                    print(self.deciles(areasI))
                    print("Elongation")
                    print(self.deciles(elongationsI))
                    print("Area / perimeter")
                    print(self.deciles(area_perimetersI))
                    print("Distance to road")
                    print(self.deciles(distToRoadsI))
                    print("Complexity")
                    print(self.deciles(complexitiesI))
                    print("Form factor")
                    print(self.deciles(formFactorsI))

            
                feat = QgsFeature()
                feat.setGeometry( geomI )
                feat.initAttributes(len(fieldsBis))
                feat.setAttribute( 0, ID )
                feat.setAttribute( 1, nb_batiments )
                if nb_batiments > 0:
                    feat.setAttribute( 2, self.mediane(areasI) )
                    feat.setAttribute( 3, self.moyenne(areasI) )
                    feat.setAttribute( 4, self.ecart_type(areasI) )
                    #feat.setAttribute( 5, self.deciles(areasI) )
                    feat.setAttribute( 6, self.mediane(elongationsI) )
                    feat.setAttribute( 7, self.moyenne(elongationsI) )
                    feat.setAttribute( 8, self.ecart_type(elongationsI))
                    #feat.setAttribute( 9, self.deciles(elongationsI) )
                    feat.setAttribute( 10, self.mediane(area_perimetersI))
                    feat.setAttribute( 11, self.moyenne(area_perimetersI))
                    feat.setAttribute( 12, self.ecart_type(area_perimetersI))
                    #feat.setAttribute( 13, self.deciles(area_perimetersI))
                    feat.setAttribute( 14, sum_areas / areaI)
                    feat.setAttribute( 15, dens_batie[indexI]/areaI)
                    feat.setAttribute( 16, self.mediane(distToRoadsI))
                    feat.setAttribute( 17, self.moyenne(distToRoadsI))
                    feat.setAttribute( 18, self.ecart_type(distToRoadsI))
                    #feat.setAttribute( 19, self.deciles(distToRoadsI))
                    feat.setAttribute( 20, dens_vegetaleI / areaI)
                    feat.setAttribute( 21, self.mediane(complexitiesI))
                    feat.setAttribute( 22, self.moyenne(complexitiesI))
                    feat.setAttribute( 23, self.ecart_type(complexitiesI))
                    #feat.setAttribute( 24, self.deciles(complexitiesI))
                    feat.setAttribute( 25, self.mediane(formFactorsI))
                    feat.setAttribute( 26, self.moyenne(formFactorsI))
                    feat.setAttribute( 27, self.ecart_type(formFactorsI))
                    #feat.setAttribute( 28, self.deciles(formFactorsI))
                    

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
                    smbr = self.compute_SMBR(geom)
                    res.append(self.compute_convexity2(geom.area(),smbr[1]))
                    i = i + 1
                    progress.setValue(i)
                ind = "convexity depending on SMBR" """
                

            QgsMapLayerRegistry.instance().addMapLayer(vl)
            QgsMapLayerRegistry.instance().addMapLayer(irisBis)
            #QMessageBox.information(self.iface.mainWindow(),ind,str(res))

            self.iface.messageBar().clearWidgets()

