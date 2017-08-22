# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'IndicMorph_dialog_base.ui'
#
# Created: Fri May 19 10:27:20 2017
#      by: PyQt4 UI code generator 4.10.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_IndicateursMorphoDialogBase(object):
    def setupUi(self, IndicateursMorphoDialogBase):
        IndicateursMorphoDialogBase.setObjectName(_fromUtf8("IndicateursMorphoDialogBase"))
        IndicateursMorphoDialogBase.resize(400, 300)
        self.button_box = QtGui.QDialogButtonBox(IndicateursMorphoDialogBase)
        self.button_box.setGeometry(QtCore.QRect(30, 240, 341, 32))
        self.button_box.setOrientation(QtCore.Qt.Horizontal)
        self.button_box.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.button_box.setObjectName(_fromUtf8("button_box"))
        self.couche = QtGui.QComboBox(IndicateursMorphoDialogBase)
        self.couche.setGeometry(QtCore.QRect(80, 60, 141, 22))
        self.couche.setObjectName(_fromUtf8("couche"))
        self.indicateur = QtGui.QComboBox(IndicateursMorphoDialogBase)
        self.indicateur.setGeometry(QtCore.QRect(80, 120, 141, 22))
        self.indicateur.setObjectName(_fromUtf8("indicateur"))
        self.label = QtGui.QLabel(IndicateursMorphoDialogBase)
        self.label.setGeometry(QtCore.QRect(70, 40, 121, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(IndicateursMorphoDialogBase)
        self.label_2.setGeometry(QtCore.QRect(70, 100, 111, 16))
        self.label_2.setObjectName(_fromUtf8("label_2"))

        self.retranslateUi(IndicateursMorphoDialogBase)
        QtCore.QObject.connect(self.button_box, QtCore.SIGNAL(_fromUtf8("accepted()")), IndicateursMorphoDialogBase.accept)
        QtCore.QObject.connect(self.button_box, QtCore.SIGNAL(_fromUtf8("rejected()")), IndicateursMorphoDialogBase.reject)
        QtCore.QMetaObject.connectSlotsByName(IndicateursMorphoDialogBase)

    def retranslateUi(self, IndicateursMorphoDialogBase):
        IndicateursMorphoDialogBase.setWindowTitle(_translate("IndicateursMorphoDialogBase", "Indicateurs morphologiques", None))
        self.label.setText(_translate("IndicateursMorphoDialogBase", "Couche à évaluer", None))
        self.label_2.setText(_translate("IndicateursMorphoDialogBase", "Indicateur à calculer", None))

