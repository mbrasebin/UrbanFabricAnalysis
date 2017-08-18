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
from PyQt5.QtWidgets import QAction, QProgressBar, QMessageBox, QComboBox
# Initialize Qt resources from file resources.py
from .resources import *
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

    def findIRIS_areas(self,geom,layer_IRIS,nom_idIRIS):
        intersections = []
        for iris in layer_IRIS.getFeatures():
            if iris.geometry().intersects(geom):
                intersections.append([iris.attribute(nom_idIRIS),iris.geometry().intersection(geom).area()])
        return intersections

    def findIRIS_line(self,geom,layer_IRIS,nom_idIRIS):
        intersections = []
        for iris in layer_IRIS.getFeatures():
            if iris.geometry().intersects(geom):
                intersections.append([iris.attribute(nom_idIRIS),iris.geometry().intersection(geom).length()])
        iris_id = 0
        length_max = 0
        for element in intersections:
            if element[1]>length_max:
                iris_id = element[0]
                length_max = element[1]
        return iris_id

    def findIRIS(self,geom,layer_IRIS,nom_idIRIS):
        intersections = self.findIRIS_areas(geom,layer_IRIS,nom_idIRIS)
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

    def compute_formFactor(self, hauteur, SMBR_width, SMBR_height):
        """
        Calcul du facteur de forme
        """
        formFactor = hauteur * 2 / (SMBR_width + SMBR_height)
        return formFactor

    def compute_formIndice(self, hauteur, area):
        """
        Calcul de l'indice de forme
        """
        formIndice = hauteur**2 / area
        return formIndice

    def fusionI(self, a_traiter, i):
        #renvoie une liste des batiments les plus proches de la rue d'un cote donne pour chaque abscisse de l'intervalle i par rapport a l'ajout de i_new

        #le batiment a_traiter est plus eloigne que le batiment i
        if i[2] <= a_traiter:
            return [i]
        else:
        
            #les 2 intervalles s'intersectent
            if a_traiter[1][0] < i[1][1] and a_traiter[1][1] > i[1][0]:
                inter = [max(i[1][0],a_traiter[1][0]),min(i[1][1],a_traiter[1][1])]
                pInf = [i[1][0],inter[0]]
                pSup = [i[1][1],inter[1]]
                if pInf[0]==pInf[1] and pSup[0]==pSup[1]:
                    return [inter]
                elif pInf[0]!=pInf[1] and pSup[0]==pSup[1]:
                    return [inter,pInf]
                elif pInf[0]==pInf[1] and pSup[0]!=pSup[1]:
                    return [inter,pSup]
                else:
                    return [inter,pInf,pSup]
            
            #pas d'intersection, le batiment a_traiter ne donne pas sur l'intervalle du batiment i
            else:
                return [i]


    def gestion_dist_rec(self,i_new,intervalles):
        #ajoute un intervalle i_new a l'ensemble des intervalles d'un cote donnant le batiment le plus proche de la rue pour ces abscisses
        if intervalles == []:
            return [i_new]
        else:
            i = intervalles[0]
            #gestion recursive de l'eventuelle partie de i_new situee avant l'intervalle i
            if i_new[1][0] < i[1][0]:
                intervalles = [i]+self.gestion_dist_rec([i_new[0],[i_new[1][0],min(i[1][0],i_new[1][1])],i_new[2]],intervalles[1:])
            #gestion recursive de l'eventuelle partie de i_new situee apres l'intervalle i
            if i_new[1][1] > i[1][1]:
                intervalles = [i]+self.gestion_dist_rec([i_new[0],[i_new[1][0],max(i[1][0],i_new[1][1])],i_new[2]],intervalles[1:])
            #gestion de l'intervalle i
            l_rempIn = self.fusionI(i_new,i)
            return l_rempIn+intervalles[1:]

    

    def gestion_distance(self, intervalles1):
        #ne conserve pour chaque partie de la rue que le batiment le plus proche d'un cote donne
        intervalles2=[]
        #on considere successivement les differents intervalles de inttervalles1 en faisant evoluer intervalles2
        for i_new in intervalles1:
            intervalles2 = self.gestion_dist_rec(i_new,intervalles2)
        return intervalles2

    def compute_landsberg(self, rue, sIndex_bati, features_bati, nom_hauteur):
        #calcule l'indicateur de landsberg pour la rue
    
        #selection des batiments proches de la rue de chaque cote
        b_rue = rue.singleSidedBuffer(500,7,QgsGeometry.SideLeft)
        b_rue2 = rue.singleSidedBuffer(500,7,QgsGeometry.SideRight)
        buffers_rue = [b_rue,b_rue2]
        #calcul de la projection de chaque batiment sur la rue pour chaque cote
        for i in [0,1]:
            buff_rue = buffers_rue[i]
            voisinage = []
            batis_id = sIndex_bati.intersects(buff_rue.boundingBox())
            for bati_id in batis_id:
                if features_bati[bati_id].intersects(buff_rue):
                    voisinage += [bati_id]
            for voisin_id in voisinage:
                voisin = features_bati[voisin_id]
                init = False
                intervalles = []
                for point in voisin.geometry().asPolygon()[0]:
                    x = rue.geometry().lineLocatePoint(point)
                    if not init:
                        mini = x
                        maxi = x
                    else:
                        mini = min(x,mini)
                        maxi = max(x,maxi)
                disR = voisin.distance(rue)
                intervalles += [voisin_id,[mini,maxi],disR]
            if i == 0:
                intervalles01 = intervalles
            else:
                intervalles11 = intervalles

        #selection des batiments sur chaque intervalle ou 2 se font face
        intervalles02 = self.gestion_distance(intervalles01)
        intervalles12 = self.gestion_distance(intervalles11)
        intervalles2 = self.gestion_cotes(intervalles11,intervalles12)

        #calcul de l'indicateur sur chaque intervalle ou 2 batiments se font face
        landsberg = 0
        for i in intervalles2 :
            hauteur = features_bati[i[0]].attribute(nom_hauteur)
            landsberg += (intervalles2[1][1]-intervalles2[1][0])*hauteur/i[2]
        landsberg = landsberg / som_int
        return landsberg
    
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

        self.dlg.bati.clear()
        self.dlg.routes.clear()
        self.dlg.vegetation.clear()
        self.dlg.iris.clear()

        #set the couche combobox items
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in layers:
            self.dlg.bati.addItem(layer.name(),layer)
            self.dlg.routes.addItem(layer.name(),layer)
            self.dlg.vegetation.addItem(layer.name(),layer)
            self.dlg.iris.addItem(layer.name(),layer)

        


        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        
        # See if OK was pressed
        if result:


            print("Bravo")
            
            #get the index of the combobox
            indexBati = self.dlg.bati.currentIndex()
            indexRoutes = self.dlg.routes.currentIndex()
            indexVegetation = self.dlg.vegetation.currentIndex()
            indexIRIS = self.dlg.iris.currentIndex()
            layer_bati = self.dlg.bati.itemData(indexBati)
            layer_routes = self.dlg.routes.itemData(indexRoutes)
            features_road = {RFeature.id(): RFeature for RFeature in layer_routes.getFeatures()}
            layer_vegetation = self.dlg.vegetation.itemData(indexVegetation)
            layer_IRIS = self.dlg.iris.itemData(indexIRIS)

            


            #definition des attributs utiles
            #HauteurBatiments
            bati_attributes = [layer_bati.attributeDisplayName(i) for i in layer_bati.attributeList()]
            h_cmbBox = QComboBox()
            h_cmbBox.show()
            for a in bati_attributes:
                h_cmbBox.addItem(a)
            h_cmbBox.showPopup()
            QMessageBox.information(self.iface.mainWindow(),"Choix de l'attribut","Hauteur Batiment")
            nom_hauteur = h_cmbBox.currentText()

            #ID Batiments
            bid_cmbBox = QComboBox()
            bid_cmbBox.show()
            for a in bati_attributes:
                bid_cmbBox.addItem(a)
            bid_cmbBox.showPopup()
            QMessageBox.information(self.iface.mainWindow(),"Choix de l'attribut","ID Batiment")
            nom_idBati = bid_cmbBox.currentText()

            #ID IRIS
            iris_attributes = [layer_IRIS.attributeDisplayName(i) for i in layer_IRIS.attributeList()]
            iris_cmbBox = QComboBox()
            iris_cmbBox.show()
            for a in iris_attributes:
                iris_cmbBox.addItem(a)
            iris_cmbBox.showPopup()
            QMessageBox.information(self.iface.mainWindow(),"Choix de l'attribut","ID IRIS")
            nom_idIRIS = iris_cmbBox.currentText()
            
            #Importance Routes
            routes_attributes = [layer_routes.attributeDisplayName(i) for i in layer_routes.attributeList()]
            imp_cmbBox = QComboBox()
            imp_cmbBox.show()
            for a in routes_attributes:
                imp_cmbBox.addItem(a)
            imp_cmbBox.showPopup()
            QMessageBox.information(self.iface.mainWindow(),"Choix de l'attribut","Importance des routes")
            nom_importance = imp_cmbBox.currentText()
            
            #Largeur Routes
            larg_cmbBox = QComboBox()
            larg_cmbBox.show()
            for a in routes_attributes:
                larg_cmbBox.addItem(a)
            larg_cmbBox.showPopup()
            QMessageBox.information(self.iface.mainWindow(),"Choix de l'attribut","Largeur des routes")
            nom_largeur = larg_cmbBox.currentText()
            
            liste_IRIS = {IFeature.attribute(nom_idIRIS) : IFeature for IFeature in layer_IRIS.getFeatures()}
            liste_IRISBatis = []
            features_bati = {BFeature.attribute(nom_idBati) : BFeature for BFeature in layer_bati.getFeatures()}
            """
            #dict
            liste_IRIS = []
            for f in layer_IRIS.getFeatures():
                n=f.attribute(nom_idIRIS)
                liste_IRIS = self.addListe(liste_IRIS,0,int(n))
            """            


            # create layer
            vl = QgsVectorLayer("Polygon", layer_bati.name(), "memory")
            pr = vl.dataProvider()

            # Enter editing mode
            vl.startEditing()

            # add fields
            fields = [
                QgsField("ID", QVariant.String),
                QgsField("area", QVariant.Double),
                QgsField("volume",QVariant.Double),
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
                QgsField("formIndice",QVariant.Double),
                QgsField("nearRoad",QVariant.String)]

            #create spatial index

            SIndex_routes = QgsSpatialIndex()
            for feat_route in layer_routes.getFeatures():
                SIndex_routes.insertFeature(feat_route)

            SIndex_bati = QgsSpatialIndex()
            for feat_bati in layer_bati.getFeatures():
                SIndex_bati.insertFeature(feat_route)
            
            # add the new measures to the features
            pr.addAttributes( fields )
            vl.updateFields()

            progressMessageBar = self.iface.messageBar().createMessage("Computing measures...")
            progress = QProgressBar()
            progress.setMaximum(layer_bati.featureCount())
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            self.iface.messageBar().pushWidget(progressMessageBar, self.iface.messageBar().INFO)

            """
            #dict
            areas = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            volumes = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            elongations = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            featureList = []
            featureListBis = []
            area_perimeters = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            dens_batie = [0 for j in range(len(liste_IRIS))]
            distToRoads = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            dens_vegetale = [0 for j in range(len(liste_IRIS))]
            complexities = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            formFactors = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            formIndices = [[liste_IRIS[j],[]] for j in range(len(liste_IRIS))]
            """

            areas = {}
            volumes = {}
            elongations = {}
            featureList = []
            featureListBis = []
            area_perimeters = {}
            dens_batie = {}
            distToRoads = {}
            dens_vegetale = {}
            complexities = {}
            formFactors = {}
            formIndices = {}
            landsberg = {}
            
                        
            
            i = 0
            
            # add features
            for f in layer_bati.getFeatures():
                geom = f.geometry()
                area = geom.area()
                perimeter = geom.length()
                hauteur = f.attribute(nom_hauteur)
                #99
                ident = f.attribute(nom_idBati)

                #recherche de l'IRIS du batiment
                iris_id = self.findIRIS(geom,layer_IRIS,nom_idIRIS)

                """
                #dict
                if iris_id != 0:
                    index_iris = self.findIndex(liste_IRIS,int(iris_id))
                """

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
                        #99
                        nRoad = f_road.attribute(nom_idBati)
                    elif(distToRoad<distToRoadMin):
                        distToRoadMin = distToRoad
                        #99
                        nRoad = f_road.attribute(nom_idBati)
                
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
                complexity = len(geom.asPolygon()[0]) - 1
                formFactor = self.compute_formFactor(hauteur, SMBR_width, SMBR_height)
                formIndice = self.compute_formIndice(hauteur, area)
                #remplissage des listes pour les calculs a l'echelle de l'IRIS
                if iris_id in liste_IRISBatis:
                    elongations[iris_id] += [elongation]
                    area_perimeters[iris_id] += [area/perimeter]
                    areas[iris_id] += [area]
                    volumes[iris_id] += [area * hauteur]
                    dens_batie[iris_id] += area*(hauteur*5/2)
                    if distToRoadMin >= 0:
                        distToRoads[iris_id] += [distToRoadMin]
                    complexities[iris_id] += [complexity]
                    formFactors[iris_id] += [formFactor]
                    formIndices[iris_id] += [formIndice]
                else:
                    liste_IRISBatis += [iris_id]
                    elongations[iris_id] = [elongation]
                    area_perimeters[iris_id] = [area/perimeter]
                    areas[iris_id] = [area]
                    volumes[iris_id] = [area * hauteur]
                    dens_batie[iris_id] = area*(hauteur*5/2)
                    if distToRoadMin >= 0:
                        distToRoads[iris_id] = [distToRoadMin]
                    complexities[iris_id] = [complexity]
                    formFactors[iris_id] = [formFactor]
                    formIndices[iris_id] = [formIndice]
                    dens_vegetale[iris_id] = 0
                    landsberg[iris_id] = []

                feat = QgsFeature()
                feat.setGeometry( geom )
                feat.initAttributes(len(fields))
                #99
                feat.setAttribute( 0, ident)
                feat.setAttribute( 1, area )
                feat.setAttribute( 2, area * hauteur)
                feat.setAttribute( 3, SMBR_area )
                feat.setAttribute( 4, SMBR_angle )
                feat.setAttribute( 5, SMBR_width )
                feat.setAttribute( 6, SMBR_height )
                feat.setAttribute( 7, convexity1 )
                feat.setAttribute( 8, convexity2 )
                feat.setAttribute( 9, elongation)
                feat.setAttribute( 10, compactness )
                feat.setAttribute( 11, area/perimeter)
                feat.setAttribute( 12, iris_id)
                if distToRoadMin >= 0:
                    feat.setAttribute( 13, distToRoadMin)
                feat.setAttribute( 14, complexity)
                feat.setAttribute( 15, formFactor)
                feat.setAttribute( 16, formIndice)
                #99
                feat.setAttribute(17, nRoad)
                featureList.append(feat)
                i += 1
                progress.setValue(i)

            pr.addFeatures (featureList)
            vl.commitChanges()

            for fVeget in layer_vegetation.getFeatures():
                geomV = fVeget.geometry()
                areaV = geomV.area()
                iris_areasV = self.findIRIS_areas(geomV,layer_IRIS,nom_idIRIS)
                for element in iris_areasV:
                    if dens_vegetale.has_key(element[0]):
                        dens_vegetale[element[0]] += element[1]

            for fRoad in layer_routes.getFeatures():
                iris_r = self.findIRIS_line(fRoad.geometry(),layer_IRIS,nom_idIRIS)
                if landsberg.has_key(iris_r):
                    landsberg[iris_r] += [self.compute_landsberg(fRoad,SIndex_bati,features_bati,nom_hauteur)]
                

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
                QgsField("volume_med",QVariant.Double),
                QgsField("volume_moy",QVariant.Double),
                QgsField("volume_ect",QVariant.Double),
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
                QgsField("formF_dec",QVariant.Double),
                QgsField("formI_med",QVariant.Double),
                QgsField("formI_moy",QVariant.Double),
                QgsField("formI_ect",QVariant.Double),
                QgsField("lands_med",QVariant.Double),
                QgsField("lands_moy",QVariant.Double),
                QgsField("lands_ect",QVariant.Double)
                ]
            
            # add the new measures to the features
            prBis.addAttributes( fieldsBis )
            irisBis.updateFields()

            for irisID in liste_IRISBatis:
                featIRIS = liste_IRIS[irisID]
                geomI = featIRIS.geometry()
                areaI = geomI.area()
                ID = featIRIS.attribute(nom_idIRIS)
                #dict   indexI = self.findIndex(liste_IRIS,int(ID))
                areasI = areas[ID]
                volumesI = volumes[ID]
                elongationsI = elongations[ID]
                area_perimetersI = area_perimeters[ID]
                nb_batiments = len(areas[ID])
                sum_areas = sum(areasI)
                distToRoadsI = distToRoads[ID]
                dens_vegetaleI = dens_vegetale[ID]
                complexitiesI = complexities[ID]
                formFactorsI = formFactors[ID]
                formIndicesI = formIndices[ID]
                landsbergI = landsberg[ID]

                if nb_batiments > 0:
                    print(ID)
                    print("Area")
                    print(self.deciles(areasI))
                    print("Volume")
                    print(self.deciles(volumesI))
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
                    feat.setAttribute( 6, self.mediane(volumesI))
                    feat.setAttribute( 7, self.moyenne(volumesI))
                    feat.setAttribute( 8, self.ecart_type(volumesI))
                    feat.setAttribute( 9, self.mediane(elongationsI) )
                    feat.setAttribute( 10, self.moyenne(elongationsI) )
                    feat.setAttribute( 11, self.ecart_type(elongationsI))
                    #feat.setAttribute( 12, self.deciles(elongationsI) )
                    feat.setAttribute( 13, self.mediane(area_perimetersI))
                    feat.setAttribute( 14, self.moyenne(area_perimetersI))
                    feat.setAttribute( 15, self.ecart_type(area_perimetersI))
                    #feat.setAttribute( 16, self.deciles(area_perimetersI))
                    feat.setAttribute( 17, sum_areas / areaI)
                    feat.setAttribute( 18, dens_batie[ID]/areaI)
                    feat.setAttribute( 19, self.mediane(distToRoadsI))
                    feat.setAttribute( 20, self.moyenne(distToRoadsI))
                    feat.setAttribute( 21, self.ecart_type(distToRoadsI))
                    #feat.setAttribute( 22, self.deciles(distToRoadsI))
                    feat.setAttribute( 23, dens_vegetaleI / areaI)
                    feat.setAttribute( 24, self.mediane(complexitiesI))
                    feat.setAttribute( 25, self.moyenne(complexitiesI))
                    feat.setAttribute( 26, self.ecart_type(complexitiesI))
                    #feat.setAttribute( 27, self.deciles(complexitiesI))
                    feat.setAttribute( 28, self.mediane(formFactorsI))
                    feat.setAttribute( 29, self.moyenne(formFactorsI))
                    feat.setAttribute( 30, self.ecart_type(formFactorsI))
                    #feat.setAttribute( 31, self.deciles(formFactorsI))
                    feat.setAttribute( 32, self.mediane(formIndicesI))
                    feat.setAttribute( 33, self.moyenne(formIndicesI))
                    feat.setAttribute( 34, self.ecart_type(formIndicesI))
                    feat.setAttribute( 35, self.mediane(landsbergI))
                    feat.setAttribute( 36, self.moyenne(landsbergI))
                    feat.setAttribute( 37, self.ecart_type(landsbergI))
                    

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

