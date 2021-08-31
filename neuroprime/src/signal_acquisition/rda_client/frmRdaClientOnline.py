# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'frmRdaClientOnline.ui'
#
# Created: Wed Jun 05 12:00:50 2013
#      by: PyQt4 UI code generator 4.5.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_frmRdaClientOnline(object):
    def setupUi(self, frmRdaClientOnline):
        frmRdaClientOnline.setObjectName("frmRdaClientOnline")
        frmRdaClientOnline.resize(314, 136)
        frmRdaClientOnline.setFrameShape(QtGui.QFrame.Panel)
        frmRdaClientOnline.setFrameShadow(QtGui.QFrame.Raised)
        self.gridLayout = QtGui.QGridLayout(frmRdaClientOnline)
        self.gridLayout.setObjectName("gridLayout")
        self.groupBoxMode = QtGui.QGroupBox(frmRdaClientOnline)
        self.groupBoxMode.setFlat(False)
        self.groupBoxMode.setCheckable(False)
        self.groupBoxMode.setObjectName("groupBoxMode")
        self.gridLayout_2 = QtGui.QGridLayout(self.groupBoxMode)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButtonConnect = QtGui.QPushButton(self.groupBoxMode)
        self.pushButtonConnect.setMinimumSize(QtCore.QSize(150, 40))
        self.pushButtonConnect.setStyleSheet("text-align: left; padding-left: 10px;")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/icons/play.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        icon.addPixmap(QtGui.QPixmap(":/icons/play_green.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.pushButtonConnect.setIcon(icon)
        self.pushButtonConnect.setIconSize(QtCore.QSize(32, 32))
        self.pushButtonConnect.setCheckable(True)
        self.pushButtonConnect.setAutoExclusive(True)
        self.pushButtonConnect.setAutoDefault(False)
        self.pushButtonConnect.setObjectName("pushButtonConnect")
        self.horizontalLayout.addWidget(self.pushButtonConnect)
        self.labelMessage = QtGui.QLabel(self.groupBoxMode)
        self.labelMessage.setAlignment(QtCore.Qt.AlignCenter)
        self.labelMessage.setObjectName("labelMessage")
        self.horizontalLayout.addWidget(self.labelMessage)
        self.gridLayout_2.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.comboBoxServerIP = QtGui.QComboBox(self.groupBoxMode)
        self.comboBoxServerIP.setEditable(True)
        self.comboBoxServerIP.setInsertPolicy(QtGui.QComboBox.NoInsert)
        self.comboBoxServerIP.setObjectName("comboBoxServerIP")
        self.comboBoxServerIP.addItem(QtCore.QString())
        self.horizontalLayout_2.addWidget(self.comboBoxServerIP)
        self.pushButtonAdd = QtGui.QPushButton(self.groupBoxMode)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButtonAdd.sizePolicy().hasHeightForWidth())
        self.pushButtonAdd.setSizePolicy(sizePolicy)
        self.pushButtonAdd.setMaximumSize(QtCore.QSize(30, 16777215))
        self.pushButtonAdd.setObjectName("pushButtonAdd")
        self.horizontalLayout_2.addWidget(self.pushButtonAdd)
        self.pushButtonRemove = QtGui.QPushButton(self.groupBoxMode)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButtonRemove.sizePolicy().hasHeightForWidth())
        self.pushButtonRemove.setSizePolicy(sizePolicy)
        self.pushButtonRemove.setMinimumSize(QtCore.QSize(0, 0))
        self.pushButtonRemove.setMaximumSize(QtCore.QSize(30, 16777215))
        self.pushButtonRemove.setObjectName("pushButtonRemove")
        self.horizontalLayout_2.addWidget(self.pushButtonRemove)
        self.gridLayout_2.addLayout(self.horizontalLayout_2, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.groupBoxMode, 0, 1, 1, 1)

        self.retranslateUi(frmRdaClientOnline)
        self.comboBoxServerIP.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(frmRdaClientOnline)

    def retranslateUi(self, frmRdaClientOnline):
        frmRdaClientOnline.setWindowTitle(QtGui.QApplication.translate("frmRdaClientOnline", "Frame", None, QtGui.QApplication.UnicodeUTF8))
        self.groupBoxMode.setTitle(QtGui.QApplication.translate("frmRdaClientOnline", "RDA Client", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonConnect.setText(QtGui.QApplication.translate("frmRdaClientOnline", "Connect", None, QtGui.QApplication.UnicodeUTF8))
        self.labelMessage.setText(QtGui.QApplication.translate("frmRdaClientOnline", "disconnected", None, QtGui.QApplication.UnicodeUTF8))
        self.comboBoxServerIP.setToolTip(QtGui.QApplication.translate("frmRdaClientOnline", "RDA Server IP or Name", None, QtGui.QApplication.UnicodeUTF8))
        self.comboBoxServerIP.setItemText(0, QtGui.QApplication.translate("frmRdaClientOnline", "localhost", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonAdd.setToolTip(QtGui.QApplication.translate("frmRdaClientOnline", "Add IP to List", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonAdd.setText(QtGui.QApplication.translate("frmRdaClientOnline", "+", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonRemove.setToolTip(QtGui.QApplication.translate("frmRdaClientOnline", "Remove IP from List", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonRemove.setText(QtGui.QApplication.translate("frmRdaClientOnline", "-", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
