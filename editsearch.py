"""
qSearch
QGIS plugin

Denis Rouzaud
denis.rouzaud@gmail.com
Feb. 2012
"""

import PyQt4
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *

from ui_editsearch import Ui_editSearch
from ui_searchitem import Ui_searchItem

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

# create the dialog to connect layers
class editSearch(QDialog, Ui_editSearch ):
	def __init__(self,iface):
		self.iface = iface
		QDialog.__init__(self)
		self.setupUi(self)
		self.layer = []
		self.settings = QSettings("qSearch","qSearch")
		QObject.connect(self.saveButton , SIGNAL( "clicked()" ) , self.saveSearches)

	def initUi(self,layer):
		self.selectButton.setEnabled(False)
		self.progressBar.setVisible(False)
		for i in range(self.itemsLayout.count()): self.itemsLayout.itemAt(i).widget().close()
		self.layer = layer
		self.layerName.setText(layer.name())
		self.selection = []
		self.items = []
		self.searchIndex = len(self.readSearches())
		self.aliasBox.setChecked(self.settings.value("onlyAlias",0).toInt()[0])
		self.layerLabel.setText("%u feature(s) currently selected in" % layer.selectedFeatureCount())

	def fields(self,aliasMode=-1):
		# create list of displayed fields
		# aliasMode: -1: auto, 0: all, 1: only alias
		if aliasMode == 0: aliasMode = False
		elif aliasMode == 1: aliasMode = True
		else: aliasMode = self.aliasBox.isChecked()
		fields = []
		for i in self.layer.dataProvider().fields():
			alias = self.layer.attributeAlias(i)
			if alias == "":
				if aliasMode is True: continue
				alias = self.layer.dataProvider().fields().get(i).name()
			fields.append({'index':i,'alias':alias})
		return fields

	@pyqtSignature("on_aliasBox_clicked()")
	def on_aliasBox_clicked(self):
		# new alias mode
		aliasMode = self.aliasBox.isChecked()
		# previous alias mode: 0: going from all to only aliases, 1 going from only aliases to all
		previousAliasMode = int( not aliasMode )
		# Look for no selection combos and remove them
		item2delete = []
		for itemIndex,item in enumerate(self.items):
			if item.fieldCombo.currentIndex() == -1:
				item.close()
				item2delete.append(itemIndex)
		self.deleteItem(item2delete)				
		# Look for fields with no aliases when going from all to only aliases
		if aliasMode is True:
			item2remove = []
			for itemIndex,item in enumerate(self.items):
				currentField = self.fields(previousAliasMode)[item.fieldCombo.currentIndex()].get('index')
				ok = False
				for i,field in enumerate(self.fields()):
					if field.get('index') == currentField:
						ok = True
						break
				if ok is False:
					item2remove.append(itemIndex)
			if len(item2remove)>0:
				reply = QMessageBox.question( self , "qSearch" , "Some of the search fields have no aliases, they will be removed. Are you sure to continue?" , QMessageBox.Yes | QMessageBox.No ,QMessageBox.No )
				if reply != QMessageBox.Yes: 
					self.aliasBox.setChecked(False)
					return	
			# remove items with no corresponding aliases
			for itemIndex in item2remove: self.items[itemIndex].close()
			self.deleteItem(item2remove)
		# Apply change		
		for itemIndex,item in enumerate(self.items):
			currentField = self.fields(previousAliasMode)[item.fieldCombo.currentIndex()].get('index')
			item.fieldCombo.clear()
			for i,field in enumerate(self.fields()):
				item.fieldCombo.addItem(field.get('alias'))	
				if field.get('index') == currentField:
					item.fieldCombo.setCurrentIndex(i)

	@pyqtSignature("on_addButton_clicked()")
	def on_addButton_clicked(self):
		itemIndex = len(self.items)
		self.items.append( searchItem(self.layer,self.fields,itemIndex) )
		QObject.connect(self.items[itemIndex],SIGNAL("itemDeleted(int)"),self.deleteItem)
		self.itemsLayout.addWidget(self.items[itemIndex])

	def deleteItem(self,item2remove):
		if type(item2remove) == int: item2remove = [item2remove]
		for offset,itemIndex in enumerate(item2remove): 
			self.items.pop(itemIndex-offset)
		if len(self.items)>0:
			self.items[0].andCombo.setEnabled(False)
		for itemIndex,item in enumerate(self.items):
			item.itemIndex = itemIndex

	def loadSearch(self,i):
		self.items = []
		searches = self.readSearches()
		self.searchIndex = i
		search = searches[i]
		self.searchName.setText(search.get('name'))
		self.aliasBox.setChecked(search.get('alias'))
		for itemIndex,item in enumerate(search.get('items')):
			idx = -1
			for i,field in enumerate(self.fields()):
				if field.get('index') == item.get('index'):
					idx = i
					break
			if idx==-1: # i.e. the field apparently does not exist anymore
				continue
			self.items.append( searchItem(self.layer,self.fields,itemIndex) )
			QObject.connect(self.items[itemIndex],SIGNAL("itemDeleted(int)"),self.deleteItem)
			self.itemsLayout.addWidget(self.items[itemIndex])
			self.items[itemIndex].andCombo.setCurrentIndex(item.get('andor'))
			self.items[itemIndex].fieldCombo.setCurrentIndex(i)
			self.items[itemIndex].operatorCombo.setCurrentIndex(item.get('operator'))
			self.items[itemIndex].valueCombo.setEditText(item.get('value'))

	def readSearches(self):
		loadSearches = self.layer.customProperty("qSearch").toString()
		if loadSearches == '':
			currentSearches = []
		else:
			exec("currentSearches = %s" % loadSearches)
		return currentSearches

	def saveSearches(self):
		saveSearch = []
		for item in self.items:
			saveSearch.append( {'andor': item.andCombo.currentIndex(),
								'index': self.fields()[item.fieldCombo.currentIndex()].get('index') ,
								'operator': item.operatorCombo.currentIndex(),
								'value': item.valueCombo.currentText() } )
		currentSearches = self.readSearches()
		if self.searchIndex > len(currentSearches)-1: currentSearches.append([])
		currentSearches[self.searchIndex] = {'name': self.searchName.text(), 'alias': int(self.aliasBox.isChecked()) ,'items': saveSearch}
		self.layer.setCustomProperty("qSearch",repr(currentSearches))
		self.emit(SIGNAL("searchSaved ()"))	
		#print currentSearches

	@pyqtSignature("on_searchButton_clicked()")
	def on_searchButton_clicked(self):
		# index of fields used for search
		fields2select = []
		for item in self.items:
			fields2select.append( self.fields()[item.fieldCombo.currentIndex()].get('index'))
		andor     = ['and','or']
		operators = ['==','!=','>=','>','<=','<','True','False','==','!=']
		# create search test
		searchCmd = ""
		for i,item in enumerate(self.items):
			if i>0: searchCmd += " %s " % andor[item.andCombo.currentIndex()]
			iOper = item.operatorCombo.currentIndex() 
			operator = operators[iOper]
			if iOper < 6: # => numeric
				searchCmd += " fieldmap[%u].toDouble()[0] %s %s " % ( fields2select[i] , operator , item.valueCombo.currentText().toUtf8() )
			elif iOper < 8: 
				searchCmd += " fieldmap[%u].toString().toUtf8().contains(\"%s\") is %s" % ( fields2select[i] , item.valueCombo.currentText().replace('"', '\\"').toUtf8(), operator )	
			elif iOper < 10: 
				searchCmd += " fieldmap[%u].toString().toUtf8() %s \"%s\" " % ( fields2select[i] , operator , item.valueCombo.currentText().replace('"', '\\"').toUtf8() )	
			print searchCmd
		# select fields, init search
		provider = self.layer.dataProvider()
		provider.select(fields2select)
		self.selection = []
		f = QgsFeature()
		# Init progress bar
		self.selectButton.setText("Select")
		self.selectButton.setEnabled(False)
		self.progressBar.setVisible(True)
		self.progressBar.setMinimum(0)
		self.progressBar.setMaximum(provider.featureCount())
		self.progressBar.setValue(0)
		k = 0
		# browse features
		try:
			while (provider.nextFeature(f)):
				k+=1
				self.progressBar.setValue(k)
				fieldmap=f.attributeMap()
				if eval(searchCmd):
					self.selection.append(f.id())
			self.selectButton.setText("Select %u features" % len(self.selection))
			if len(self.selection)>0:
				self.selectButton.setEnabled(True)
		except NameError:
			QMessageBox.warning( self.iface.mainWindow() , "qSearch","If you are trying to detect text, you should use text equals." )
		except SyntaxError:
			QMessageBox.warning( self.iface.mainWindow() , "qSearch","If you are trying to detect text, you should use text equals." )
		self.progressBar.setVisible(False)
			
	@pyqtSignature("on_selectButton_clicked()")
	def on_selectButton_clicked(self):
		selection = []
		if self.addCurrentBox.isChecked():
			selection = self.layer.selectedFeaturesIds()
		selection.extend( self.selection )
		self.layer.setSelectedFeatures(selection)
		self.layerLabel.setText("%u feature(s) currently selected in" % self.layer.selectedFeatureCount())

class searchItem(QFrame, Ui_searchItem):
	def __init__(self,layer,fields,itemIndex):
		QFrame.__init__(self)
		self.setupUi(self)
		self.layer = layer
		self.fields = fields
		self.itemIndex = itemIndex
		self.settings = QSettings("qSearch","qSearch")
		if itemIndex > 0: self.andCombo.setEnabled(True)
		for f in fields(): self.fieldCombo.addItem(f.get('alias'))

	@pyqtSignature("on_fieldCombo_currentIndexChanged(int)")
	def on_fieldCombo_currentIndexChanged(self,i):
		if i < 0: return
		self.valueCombo.clear()
		ix = self.fields()[i].get('index')
		maxUnique = self.settings.value("maxUnique",30).toInt()[0]
		for value in self.layer.dataProvider().uniqueValues(ix,maxUnique):
			self.valueCombo.addItem(value.toString())

	@pyqtSignature("on_deleteButton_clicked()")
	def on_deleteButton_clicked(self):
		self.close()
		self.emit(SIGNAL("itemDeleted(int)"),self.itemIndex)
