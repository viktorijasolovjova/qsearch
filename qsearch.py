"""
qSearch
QGIS plugin

Denis Rouzaud
denis.rouzaud@gmail.com
Feb. 2012
"""
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

import resources

from chooselayer import chooseLayer
from editsearch import editSearch
from settings import settings

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class qSearch():
	def __init__(self, iface):
		# Save reference to the QGIS interface
		self.iface = iface
		# load searches when new layers are loaded
		QObject.connect(self.iface.mapCanvas() , SIGNAL("layersChanged ()") , self.loadSearch ) 
		self.chooseLayerDialog = chooseLayer(self.iface)
		self.chooseeditSearch  = editSearch(self.iface)
		
	def initGui(self):
		self.newSearchAction = QAction(QIcon(":/plugins/qsearch/icons/search.png"),"new search", self.iface.mainWindow())
		QObject.connect(self.newSearchAction, SIGNAL("triggered()"), self.newSearch)
		self.iface.addToolBarIcon(self.newSearchAction)
		self.iface.addPluginToMenu("&qSearch", self.newSearchAction)	
		# settings
		self.uisettings = settings(self.iface)
		self.uisettingsAction = QAction("settings", self.iface.mainWindow())
		QObject.connect(self.uisettingsAction, SIGNAL("triggered()"), self.uisettings.exec_)
		self.iface.addPluginToMenu("&qSearch", self.uisettingsAction)	
				
	def unload(self):
		# Remove the plugin menu item and icon
		self.iface.removePluginMenu("&qSearch",self.newSearchAction)
		
	def newSearch(self):
		if self.chooseLayerDialog.exec_():
			self.chooseeditSearch.setLayer(self.chooseLayerDialog.selectedLayer())
			self.chooseeditSearch.exec_()
			#print self.chooseeditSearch.searchValue.currentText()
	
	def loadSearch(self):
		for layer in self.iface.legendInterface().layers():
			i = 0
			while layer.customProperty("qSearch%u" % i, "").toString() != "":
				print "load qSearch for layer %s" % layer.name()
				i += 1
		
