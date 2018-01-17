# Bridge Batch Rename in Maya by Nichgon ver0.1

from Qt import QtCore, QtWidgets, QtGui, QtCompat
import maya.OpenMayaUI as omui
import maya.cmds as cmds
from functools import partial
import os,re,json,copy

def getMayaWindow():
    pointer = omui.MQtUtil.mainWindow()
    return QtCompat.wrapInstance(long(pointer), QtWidgets.QWidget)
    
# PySide doesn't have setCurrentText method so we define it
def setCurrentText(self, text):
    index = self.findText(text)
    if index != -1:
        self.setCurrentIndex(index)
    else:
        self.setEditText(text)
        
QtWidgets.QComboBox.setCurrentText = setCurrentText

class inputWidget(QtWidgets.QWidget):

    def __init__(self,type='H'):
        super(inputWidget,self).__init__()
        if type == 'H':
            self.setLayout(QtWidgets.QHBoxLayout())
        elif type == 'V':
            self.setLayout(QtWidgets.QVBoxLayout())
        else:
            raise Exception('Cannot find layout type')
        self.layout().setAlignment(QtCore.Qt.AlignLeft)
        self.layout().setContentsMargins(0,0,0,0)
        self.layout().setSpacing(0)

class generatorWidget(QtWidgets.QWidget):
    # Signal emitted when self.setting is changed
    settingChanged = QtCore.Signal(dict)
    def __init__(self):
        super(generatorWidget,self).__init__()
        self.setting = {}
        self.buildUI()
        
    def buildUI(self):
    
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(0,0,2,0) #Right margin
        self.layout().setSpacing(1)
        
        # Add container1 for every generator type except String Substitution
        self.container1_widget = QtWidgets.QWidget()
        self.container1 = QtWidgets.QHBoxLayout(self.container1_widget)
        self.container1.setContentsMargins(0,0,0,0)
        self.container1.setSpacing(7)
        self.container1.setAlignment(QtCore.Qt.AlignLeft)
        # Add container2 for String Substitution generator
        self.container2_widget = QtWidgets.QWidget()
        self.container2 = QtWidgets.QHBoxLayout(self.container2_widget)
        self.container2.setContentsMargins(0,0,0,4) #Bottom margin
        self.container2.setSpacing(7)
        self.container2.setAlignment(QtCore.Qt.AlignLeft)
        
        self.layout().addWidget(self.container1_widget)
        self.layout().addWidget(self.container2_widget)
        
        def generatorTypeUI():
            self.generatorType = QtWidgets.QComboBox()
            self.generatorType.setFixedSize(182,22)
            self.generatorType.addItem('Text')
            self.generatorType.addItem('Current Object Name')
            self.generatorType.addItem('Current Object Type')
            self.generatorType.addItem('Parent Name')
            self.generatorType.addItem('Sequence Number')
            self.generatorType.addItem('Sequence Letter')
            self.generatorType.addItem('String Substitution')
            self.generatorType.currentIndexChanged.connect(onTypeChanged)
            self.container1.addWidget(self.generatorType)
            
        def onTypeChanged():
        
            def changeVisibility(text=0,crtName=0,crtType=0,parntName=0,sqNum=0,sqLt=0,strSub=0):
                self.gn_text.setVisible(text)
                self.gn_crtName.setVisible(crtName)
                self.gn_crtType.setVisible(crtType)
                self.gn_parntName.setVisible(parntName)
                self.gn_sqNum.setVisible(sqNum)
                self.gn_sqLt.setVisible(sqLt)
                self.container2_widget.setVisible(strSub)
                self.gn_strSub1.setVisible(strSub)
                self.gn_strSub2.setVisible(strSub)
                
            type = str(self.generatorType.currentText())
            
            if type == 'Text':
                defaultSetting = {'type':'Text','val1':''}
                changeVisibility(text=1)
            elif type == 'Current Object Name':
                defaultSetting = {'type':'Current Object Name','format':'Original Case'}
                changeVisibility(crtName=1)
            elif type == 'Current Object Type':
                defaultSetting = {'type':'Current Object Type','format':'Original Case'}
                changeVisibility(crtType=1)
            elif type == 'Parent Name':
                defaultSetting = {'type':'Parent Name','format':'Original Case'}
                changeVisibility(parntName=1)
            elif type == 'Sequence Number':
                defaultSetting = {'type':'Sequence Number','val1':'1','format':'One Digit'}
                changeVisibility(sqNum=1)
            elif type == 'Sequence Letter':
                defaultSetting = {'type':'Sequence Letter','val1':'a','format':'UPPERCASE'}
                changeVisibility(sqLt=1)
            elif type == 'String Substitution':
                defaultSetting = {'type':'String Substitution','val1':'','val2':'','format':'Original Name','opt1':False,'opt2':False,'opt3':False}
                changeVisibility(strSub=1)
            else:
                raise Exception('Cannot find generator type')
                
            self.setSetting(defaultSetting)
            self.settingChanged.emit(self.setting)

        def inputUI():
            
            def setRegEx(regex,qline):
               # Maya node naming regex = "[a-zA-Z_][a-zA-Z0-9_]*" (No number at begin character)
               # If new name begin with [0-9] then warns user
               regex = QtCore.QRegExp(regex)
               text_validator = QtGui.QRegExpValidator(regex, qline)
               qline.setValidator(text_validator)
                
            attrWidth = 174
            attrHeight = 22
            attrHeightC = 22
            spacing = 5
            #===Text=========================================================================================
            def onTextValueChanged():
                self.setting['val1'] = str(self.gn_text_value.text())
                self.settingChanged.emit(self.setting)
            self.gn_text = inputWidget()
            self.gn_text_value = QtWidgets.QLineEdit()
            self.gn_text_value.setPlaceholderText("Type Text")
            self.gn_text_value.setFixedSize(attrWidth,attrHeight)
            self.gn_text_value.textChanged.connect(onTextValueChanged)
            setRegEx('[a-zA-Z0-9_]*',self.gn_text_value)
            self.gn_text.layout().addWidget(self.gn_text_value)
            self.container1.addWidget(self.gn_text)
            #===Current Object Name==========================================================================
            def onCurNameFormatChanged():
                self.setting['format'] = str(self.gn_crtName_format.currentText())
                self.settingChanged.emit(self.setting)
            self.gn_crtName = inputWidget()
            self.gn_crtName_format = QtWidgets.QComboBox()
            self.gn_crtName_format.setFixedSize(attrWidth,attrHeightC)
            self.gn_crtName_format.addItem('Original Case')
            self.gn_crtName_format.addItem('UPPERCASE')
            self.gn_crtName_format.addItem('lowercase')
            self.gn_crtName_format.currentIndexChanged.connect(onCurNameFormatChanged)
            self.gn_crtName.layout().addWidget(self.gn_crtName_format)
            self.container1.addWidget(self.gn_crtName)
            #===Current Object Type==========================================================================
            def onCurTypeFormatChanged():
                self.setting['format'] = str(self.gn_crtType_format.currentText())
                self.settingChanged.emit(self.setting)
            self.gn_crtType = inputWidget()
            self.gn_crtType_format = QtWidgets.QComboBox()
            self.gn_crtType_format.setFixedSize(attrWidth,attrHeightC)
            self.gn_crtType_format.addItem('Original Case')
            self.gn_crtType_format.addItem('UPPERCASE')
            self.gn_crtType_format.addItem('lowercase')
            self.gn_crtType_format.currentIndexChanged.connect(onCurTypeFormatChanged)
            self.gn_crtType.layout().addWidget(self.gn_crtType_format)
            self.container1.addWidget(self.gn_crtType)
            #===Parent Name==================================================================================
            def onParntNameFormatChanged():
                self.setting['format'] = str(self.gn_parntName_format.currentText())
                self.settingChanged.emit(self.setting)
            self.gn_parntName = inputWidget()
            self.gn_parntName_format = QtWidgets.QComboBox()
            self.gn_parntName_format.setFixedSize(attrWidth,attrHeightC)
            self.gn_parntName_format.addItem('Original Case')
            self.gn_parntName_format.addItem('UPPERCASE')
            self.gn_parntName_format.addItem('lowercase')
            self.gn_parntName_format.currentIndexChanged.connect(onParntNameFormatChanged)
            self.gn_parntName.layout().addWidget(self.gn_parntName_format)
            self.container1.addWidget(self.gn_parntName)
            #===Sequence Number==============================================================================
            def onSqNumValueChanged():
                if len(self.gn_sqNum_value.text()) > 0:
                    self.setting['val1'] = str(self.gn_sqNum_value.text())
                else:
                    self.setting['val1'] = '0'
                self.settingChanged.emit(self.setting)
            def onSqNumValueEditFin():
                if len(self.gn_sqNum_value.text()) == 0:
                    self.gn_sqNum_value.setText('0')
                    self.setting['val1'] = '0'
                self.settingChanged.emit(self.setting)
            def onSqNumFormatChanged():
                self.setting['format'] = str(self.gn_sqNum_format.currentText())
                self.settingChanged.emit(self.setting)
            self.gn_sqNum = inputWidget()
            self.gn_sqNum.layout().setSpacing(spacing)
            self.gn_sqNum_value = QtWidgets.QLineEdit()
            self.gn_sqNum_value.setFixedSize(attrWidth,attrHeight)
            setRegEx('\d*',self.gn_sqNum_value)
            self.gn_sqNum_value.setMaxLength(6)
            self.gn_sqNum_value.textChanged.connect(onSqNumValueChanged)
            self.gn_sqNum_value.editingFinished.connect(onSqNumValueEditFin)
            self.gn_sqNum_format = QtWidgets.QComboBox()
            self.gn_sqNum_format.setFixedSize(attrWidth,attrHeightC)
            self.gn_sqNum_format.addItem('One Digit')
            self.gn_sqNum_format.addItem('Two Digits')
            self.gn_sqNum_format.addItem('Three Digits')
            self.gn_sqNum_format.addItem('Four Digits')
            self.gn_sqNum_format.addItem('Five Digits')
            self.gn_sqNum_format.addItem('Six Digits')
            self.gn_sqNum_format.currentIndexChanged.connect(onSqNumFormatChanged)
            self.gn_sqNum.layout().addWidget(self.gn_sqNum_value)
            self.gn_sqNum.layout().addWidget(self.gn_sqNum_format)
            self.container1.addWidget(self.gn_sqNum)
            #===Sequence Letter==============================================================================
            def onSqLtValueChanged():
                if len(self.gn_sqLt_value.text()) > 0:
                    self.setting['val1'] = str(self.gn_sqLt_value.text())
                else:
                    self.setting['val1'] = 'a'
                self.settingChanged.emit(self.setting)
            def onSqLtValueEditFin():
                if len(self.gn_sqLt_value.text()) == 0:
                    self.gn_sqLt_value.setText('a')
                    self.setting['val1'] = 'a'
                self.settingChanged.emit(self.setting)
            def onSqLtFormatChanged():
                self.setting['format'] = str(self.gn_sqLt_format.currentText())
                if self.setting['format'] == 'UPPERCASE':
                    font.setCapitalization(QtGui.QFont.AllUppercase)
                elif self.setting['format'] == 'lowercase':
                    font.setCapitalization(QtGui.QFont.AllLowercase)
                else:
                    raise Exception('Cannot find format')
                self.gn_sqLt_value.setFont(font)
                self.settingChanged.emit(self.setting)
            font = QtGui.QFont()
            self.gn_sqLt = inputWidget()
            self.gn_sqLt.layout().setSpacing(spacing)
            self.gn_sqLt_value = QtWidgets.QLineEdit()
            self.gn_sqLt_value.setFixedSize(attrWidth,attrHeight)
            self.gn_sqLt_value.setFont(font)
            self.gn_sqLt_value.textChanged.connect(onSqLtValueChanged)
            self.gn_sqLt_value.editingFinished.connect(onSqLtValueEditFin)
            setRegEx('[a-zA-Z]*',self.gn_sqLt_value) 
            self.gn_sqLt_value.setMaxLength(1) # Assign RegEx and maxLength this way, editingFinished won't break
            self.gn_sqLt_format = QtWidgets.QComboBox()
            self.gn_sqLt_format.setFixedSize(attrWidth,attrHeightC)
            self.gn_sqLt_format.addItem('UPPERCASE')
            self.gn_sqLt_format.addItem('lowercase')
            self.gn_sqLt_format.currentIndexChanged.connect(onSqLtFormatChanged)
            self.gn_sqLt.layout().addWidget(self.gn_sqLt_value)
            self.gn_sqLt.layout().addWidget(self.gn_sqLt_format)
            self.container1.addWidget(self.gn_sqLt)
            #===String Substitution==========================================================================
            def onStrSubFormatChanged():
                self.setting['format'] = str(self.gn_strSub_format.currentText())
                self.settingChanged.emit(self.setting)
            def onStrSubFindValChanged():
                self.setting['val1'] = str(self.gn_strSub_find.text())
                self.settingChanged.emit(self.setting)
            def onStrSubReplaceValChanged():
                self.setting['val2'] = str(self.gn_strSub_replaceWith.text())
                self.settingChanged.emit(self.setting)
            def onStrSubIgnoreCaseChanged():
                self.setting['opt1'] = self.gn_strSub_ignoreCase.isChecked()
                self.settingChanged.emit(self.setting)
            def onStrSubReplaceAllChanged():
                self.setting['opt2'] = self.gn_strSub_replaceAll.isChecked()
                self.settingChanged.emit(self.setting)
            def onStrSubUseRegExChanged():
                self.setting['opt3'] = self.gn_strSub_useRegularExpression.isChecked()
                self.settingChanged.emit(self.setting)
            container2_mL = 48
            attrWidthFnRp = 177
            self.gn_strSub1 = inputWidget()
            self.gn_strSub2 = inputWidget(type='V')
            self.gn_strSub2.layout().setSpacing(spacing)
            self.gn_strSub2_1 = inputWidget()
            self.gn_strSub2_1.layout().setContentsMargins(container2_mL,0,0,0)
            self.gn_strSub2_1.layout().setSpacing(10)
            self.gn_strSub2_2 = inputWidget()
            self.gn_strSub2_2.layout().setContentsMargins(container2_mL,0,0,0)
            self.gn_strSub2_2.layout().setSpacing(15)
            self.gn_strSub_format = QtWidgets.QComboBox()
            self.gn_strSub_format.setFixedSize(attrWidth,attrHeightC)
            self.gn_strSub_format.addItem('Original Name')
            self.gn_strSub_format.addItem('Intermediate Name')
            self.gn_strSub_format.currentIndexChanged.connect(onStrSubFormatChanged)
            self.gn_strSub_findLabel = QtWidgets.QLabel('Find: ')
            self.gn_strSub_findLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
            self.gn_strSub_find = QtWidgets.QLineEdit()
            self.gn_strSub_find.setPlaceholderText("Type Text")
            setRegEx(r'[a-zA-Z0-9 ./<>?,;:"\'`!@#$%^&*()\\[\]{}_+=|\\-]+',self.gn_strSub_find)
            self.gn_strSub_find.setFixedSize(attrWidthFnRp,attrHeight)
            self.gn_strSub_find.textChanged.connect(onStrSubFindValChanged)
            self.gn_strSub_replaceWithLabel = QtWidgets.QLabel('Repalce with: ')
            self.gn_strSub_replaceWithLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
            self.gn_strSub_replaceWith = QtWidgets.QLineEdit()
            self.gn_strSub_replaceWith.setPlaceholderText("Type Text")
            setRegEx('[a-zA-Z0-9_]*',self.gn_strSub_replaceWith)
            self.gn_strSub_replaceWith.setFixedSize(attrWidthFnRp,attrHeight)
            self.gn_strSub_replaceWith.textChanged.connect(onStrSubReplaceValChanged)
            self.gn_strSub_ignoreCase = QtWidgets.QCheckBox('Ignore Case')
            self.gn_strSub_ignoreCase.setFocusPolicy(QtCore.Qt.StrongFocus)
            self.gn_strSub_ignoreCase.stateChanged.connect(onStrSubIgnoreCaseChanged)
            self.gn_strSub_replaceAll = QtWidgets.QCheckBox('Replace All')
            self.gn_strSub_replaceAll.setFocusPolicy(QtCore.Qt.StrongFocus)
            self.gn_strSub_replaceAll.stateChanged.connect(onStrSubReplaceAllChanged)
            self.gn_strSub_useRegularExpression = QtWidgets.QCheckBox('Use Regular Expression')
            self.gn_strSub_useRegularExpression.setFocusPolicy(QtCore.Qt.StrongFocus)
            self.gn_strSub_useRegularExpression.stateChanged.connect(onStrSubUseRegExChanged)
            self.gn_strSub1.layout().addWidget(self.gn_strSub_format)
            self.gn_strSub2.layout().addWidget(self.gn_strSub2_1)
            self.gn_strSub2.layout().addWidget(self.gn_strSub2_2)
            self.gn_strSub2_1.layout().addWidget(self.gn_strSub_findLabel)
            self.gn_strSub2_1.layout().addWidget(self.gn_strSub_find)
            self.gn_strSub2_1.layout().addWidget(self.gn_strSub_replaceWithLabel)
            self.gn_strSub2_1.layout().addWidget(self.gn_strSub_replaceWith)
            self.gn_strSub2_2.layout().addWidget(self.gn_strSub_ignoreCase)
            self.gn_strSub2_2.layout().addWidget(self.gn_strSub_replaceAll)
            self.gn_strSub2_2.layout().addWidget(self.gn_strSub_useRegularExpression)
            self.container1.addWidget(self.gn_strSub1)
            self.container2.addWidget(self.gn_strSub2)
            #================================================================================================
            # Initiate default generator type
            onTypeChanged()

        def buttonUI():
            font = QtGui.QFont()
            font.setFamily('MS Mincho')
            font.setPixelSize(24)
            self.removeButton = QtWidgets.QPushButton('-')
            self.removeButton.setFixedSize(20,20)
            self.removeButton.setFont(font)
            self.addButton = QtWidgets.QPushButton('+')
            self.addButton.setFixedSize(20,20)
            self.addButton.setFont(font)
            self.container1.addStretch()
            self.container1.addWidget(self.removeButton)
            self.container1.addWidget(self.addButton)
            
        def setMoveCursor():
            self.setCursor(QtCore.Qt.SizeAllCursor)
            self.generatorType.setCursor(QtCore.Qt.ArrowCursor)
            self.removeButton.setCursor(QtCore.Qt.ArrowCursor)
            self.addButton.setCursor(QtCore.Qt.ArrowCursor)
            self.gn_crtName_format.setCursor(QtCore.Qt.ArrowCursor)
            self.gn_crtType_format.setCursor(QtCore.Qt.ArrowCursor)
            self.gn_parntName_format.setCursor(QtCore.Qt.ArrowCursor)
            self.gn_sqNum_format.setCursor(QtCore.Qt.ArrowCursor)
            self.gn_sqLt_format.setCursor(QtCore.Qt.ArrowCursor)
            self.gn_strSub_format.setCursor(QtCore.Qt.ArrowCursor)
            self.gn_strSub_findLabel.setCursor(QtCore.Qt.ArrowCursor)
            self.gn_strSub_replaceWithLabel.setCursor(QtCore.Qt.ArrowCursor)
            self.gn_strSub_ignoreCase.setCursor(QtCore.Qt.ArrowCursor)
            self.gn_strSub_replaceAll.setCursor(QtCore.Qt.ArrowCursor)
            self.gn_strSub_useRegularExpression.setCursor(QtCore.Qt.ArrowCursor)
            
        generatorTypeUI()
        inputUI()
        buttonUI()
        setMoveCursor()
            
    def setSetting(self,setting):
        self.setting = setting
        type = setting['type']
        # print type
        # print self.generatorType.currentText()
        # print self.generatorType.findText(type)
        if self.generatorType.currentText() != type:
            self.generatorType.setCurrentText(type)
            
        if type == 'Text':
            self.gn_text_value.setText(setting['val1'])
        elif type == 'Current Object Name':
            self.gn_crtName_format.setCurrentText(setting['format'])
        elif type == 'Current Object Type':
            self.gn_crtType_format.setCurrentText(setting['format'])
        elif type == 'Parent Name':
            self.gn_parntName_format.setCurrentText(setting['format'])
        elif type == 'Sequence Number':
            self.gn_sqNum_value.setText(setting['val1'])
            self.gn_sqNum_format.setCurrentText(setting['format'])
        elif type == 'Sequence Letter':
            font = QtGui.QFont()
            if setting['format'] == 'UPPERCASE':
                font.setCapitalization(QtGui.QFont.AllUppercase)
            elif setting['format'] == 'lowercase':
                font.setCapitalization(QtGui.QFont.AllLowercasecase)
            self.gn_sqLt_value.setFont(font)
            self.gn_sqLt_value.setText(setting['val1'])
            self.gn_sqLt_format.setCurrentText(setting['format'])
        elif type == 'String Substitution':
            self.gn_strSub_format.setCurrentText(setting['format'])
            self.gn_strSub_find.setText(setting['val1'])
            self.gn_strSub_replaceWith.setText(setting['val2'])
            self.gn_strSub_ignoreCase.setChecked(setting['opt1'])
            self.gn_strSub_replaceAll.setChecked(setting['opt2'])
            self.gn_strSub_useRegularExpression.setChecked(setting['opt3'])
        else:
            raise Exception('Cannot find generator type')
        
    def getSizeHint(self):
        return self.sizeHint()
        
    def getSetting(self):
        return self.setting
        
class ElidedLabel(QtWidgets.QLabel):

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        metrics = QtGui.QFontMetrics(self.font())
        elided = metrics.elidedText(self.text(), QtCore.Qt.ElideMiddle, self.width())
        painter.drawText(self.rect(), self.alignment(), elided)

class previewItem(QtWidgets.QWidget):

    def __init__(self,crtName,newName):
        super(previewItem,self).__init__()
        self.buildUI(crtName,newName)
        
    def buildUI(self,crtName,newName):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(5,3,5,3)
        self.layout().setSpacing(0)
        
        self.crtName = ElidedLabel(crtName)
        self.crtName.setSizePolicy(QtWidgets.QSizePolicy.Ignored,QtWidgets.QSizePolicy.Preferred)
        self.newName = ElidedLabel('->  '+newName)
        self.newName.setSizePolicy(QtWidgets.QSizePolicy.Ignored,QtWidgets.QSizePolicy.Preferred)
        self.layout().addWidget(self.crtName)
        self.layout().addWidget(self.newName)
        
    def getCrtName(self):
        return self.crtName.text()

    def getNewName(self):  
        return self.newName.text()[4:]
        
class previewDialog(QtWidgets.QDialog):

    def __init__(self, batchRenameUI):
        name = "previewDialog"
        # Check for existing window
        if cmds.window(name, query=True, exists=True):
            cmds.deleteUI(name, wnd=True)
        
        # Assign dialog to be child of batchRenameUI
        super(previewDialog,self).__init__(batchRenameUI)
        
        # Set attribute
        self.setObjectName(name)
        self.setWindowTitle("Preview")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumSize(400,200)
        self.resize(600,300)
        self.setSizeGripEnabled(True)
        self.setModal(True)
        
        self.buildUI()
        self.connectInterface()
        
    def buildUI(self):
        buttonWidth = 102
        buttonHeight = 22
        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setContentsMargins(8,8,8,8)
        self.layout().setSpacing(10)
        
        self.list = QtWidgets.QListWidget()
        self.list.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.list.setFocusPolicy(QtCore.Qt.NoFocus)
        self.list.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel) # Get rid of blank area at the bottom
        self.list.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        buttonWidget = QtWidgets.QWidget()
        buttonWidget.setLayout(QtWidgets.QHBoxLayout())
        buttonWidget.layout().setContentsMargins(5,0,5,10)
        buttonWidget.layout().setSpacing(7)
        self.exportButton = QtWidgets.QPushButton('Export to CSV')
        self.exportButton.setFixedSize(buttonWidth,buttonHeight)
        font = QtGui.QFont()
        font.setPixelSize(11)
        self.guideLabel = QtWidgets.QLabel()
        self.guideLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.guideLabel.setFont(font)
        self.okButton = QtWidgets.QPushButton('OK')
        self.okButton.setFixedSize(buttonWidth,buttonHeight)
        buttonWidget.layout().addWidget(self.exportButton)
        buttonWidget.layout().addWidget(self.guideLabel)
        buttonWidget.layout().addWidget(self.okButton)
        
        self.layout().addWidget(self.list)
        self.layout().addWidget(buttonWidget)
        
    def addItem(self,crtName,newName):
        prevItem = previewItem(crtName,newName)
        item = QtWidgets.QListWidgetItem()
        item.setSizeHint(QtCore.QSize(0, prevItem.sizeHint().height()))
        self.list.addItem(item)
        self.list.setItemWidget(item, prevItem)
        
    def findItem(self,newName):
        for row in range(self.list.count()):
            item = self.list.item(row)
            prevItem = self.list.itemWidget(item)
            if prevItem.getNewName() == newName:
                return row
        else:
            return -1
        
    def updateGuide(self):
        text = 'will be renamed'
        if self.list.count() == 0: text = 'No objects '+text
        elif self.list.count() == 1: text = 'One object '+text
        else: text = '{} objects '.format(self.list.count())+text
        self.guideLabel.setText(text)
        
    def clear(self):
        # Permanently delete all items
        self.list.clear()
        
    def exportCSV(self):
        # Prompt save file dialog
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.AnyFile)
        dialog.setNameFilter('*.csv')
        dialog.setAcceptMode(QtWidgets.QFileDialog.AcceptSave)
        dialog.selectFile("Untitled.csv")
        dialog.setDirectory(".")
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            fileName = dialog.selectedFiles()[0]
            if fileName:
                # Write CSV file
                with open(fileName,'w') as file:
                    for row in range(self.list.count()):
                        item = self.list.item(row)
                        csvRow = '{},{}\n'.format(self.list.itemWidget(item).getCrtName(),self.list.itemWidget(item).getNewName())
                        file.write(csvRow)
        
    def connectInterface(self):
        self.okButton.clicked.connect(self.close)
        self.exportButton.clicked.connect(self.exportCSV)
        
class saveDialog(QtWidgets.QDialog):

    def __init__(self, batchRenameUI):
        name = "saveDialog"
        # Check for existing window
        if cmds.window(name, query=True, exists=True):
            cmds.deleteUI(name, wnd=True)
        
        # Assign dialog to be child of batchRenameUI
        super(saveDialog,self).__init__(batchRenameUI)
        
        # Set attribute
        self.setObjectName(name)
        self.setWindowTitle("Input Preset Name")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.setFixedSize(370,78)
        self.setModal(True)
        
        self.buildUI()
        self.connectInterface()
        
    def buildUI(self):
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setAlignment(QtCore.Qt.AlignTop)
        self.layout().setContentsMargins(11,11,11,11)
        self.layout().setSpacing(14)
        
        inputWidget = QtWidgets.QWidget()
        inputWidget.setLayout(QtWidgets.QHBoxLayout())
        inputWidget.layout().setAlignment(QtCore.Qt.AlignTop)
        inputWidget.layout().setContentsMargins(0,0,0,0)
        inputWidget.layout().setSpacing(7)
        inputLabel = QtWidgets.QLabel('Input:')
        self.inputLine = QtWidgets.QLineEdit()
        regex = QtCore.QRegExp(r'[a-zA-Z0-9 .,;\'`!@#$%^&()\[\]{}_+=-]+') # Except /\:*?"<>|
        text_validator = QtGui.QRegExpValidator(regex, self.inputLine)
        self.inputLine.setValidator(text_validator)
        inputWidget.layout().addWidget(inputLabel)
        inputWidget.layout().addWidget(self.inputLine)
        
        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Fixed)
        self.buttonBox.setFixedSize(90,50)
        self.buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        
        self.layout().addWidget(inputWidget)
        self.layout().addWidget(self.buttonBox)
        
    def connectInterface(self):
        self.inputLine.textChanged.connect(self.onInputChanged)
        
    def onInputChanged(self):
        if len(self.inputLine.text()) == 0:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        
    def setInput(self,presetName):
        self.inputLine.setText(presetName)
        
    def getInput(self):
        return self.inputLine.text()
        
    def selectAll(self):
        self.inputLine.selectAll()

class batchRenameUI(QtWidgets.QDialog):
    settingsFolder = 'batchRenameSettings'
    crtSettings = []
    
    def __init__(self, parent=getMayaWindow()):
        name = "batchRenameUI"
        # Check for existing window
        if cmds.window(name, query=True, exists=True):
            cmds.deleteUI(name, wnd=True)
            
        super(batchRenameUI,self).__init__(parent)
        
        # Set attribute
        self.setObjectName(name)
        self.setWindowTitle("Batch Rename")
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        self.settingDirectory = os.path.abspath(os.path.join(cmds.internalVar(upd=True),self.settingsFolder))
        self.settings_path = os.path.join(os.getenv('HOME'), "settingsFile.ini")
        
        # Store selection
        self.selection = cmds.ls(selection=True,objectsOnly=True,long=True)
        
        # Create script job
        self.SCRIPT_JOB_NUMBER = cmds.scriptJob(event=['SelectionChanged',self.onSelectionChanged], protected=True)
        
        self.initUI()
        self.buildUI()
        self.connectInterface()
        self.updateGuide()
        self.updateRenameButton()
        
    def initUI(self):
        currentDir = os.path.dirname(__file__)
        file = os.path.abspath(os.path.join(currentDir,'batchRename.ui'))
        self.ui = QtCompat.loadUi(uifile=file, baseinstance=QtWidgets.QWidget())
        
        # Add loaded ui file to our main window
        self.centralLayout = QtWidgets.QVBoxLayout(self)
        self.centralLayout.setContentsMargins(0, 0, 0, 0)
        self.centralLayout.setAlignment(QtCore.Qt.AlignAbsolute)
        self.centralLayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.centralLayout.addWidget(self.ui)
        
        # Restore window's previous geometry from file
        if os.path.exists(self.settings_path):
            settings_obj = QtCore.QSettings(self.settings_path, QtCore.QSettings.IniFormat)
            self.restoreGeometry(settings_obj.value("batchRename_windowGeometry"))
        
        # Get size form .ui file and set window fixed size
        self.ui.setLayout(QtWidgets.QHBoxLayout())
        self.ui.layout().setContentsMargins(11,11,11,14)
        self.ui.layout().setSpacing(20)
        self.default_window_width = self.ui.sizeHint().width()
        self.default_window_height = self.ui.sizeHint().height()
        self.setFixedSize(self.default_window_width,self.default_window_height)
        
    def buildUI(self):
        self.window_width = self.default_window_width
        self.window_height = self.default_window_height
        self.generatorList_height = 0
        self.generatorItemMargin = 9
        self.generatorDefaultHeight = None
        self.modifiedPreset = ''
        
        def configLabel():
            font = QtGui.QFont()
            font.setBold(True)
            font2 = QtGui.QFont()
            font2.setStrikeOut(True)
            self.crtName = ElidedLabel(self.ui.preview_group)
            self.crtName.setFont(font)
            self.crtName.setSizePolicy(QtWidgets.QSizePolicy.Ignored,QtWidgets.QSizePolicy.Preferred)
            newNameWidget = QtWidgets.QWidget(self.ui.preview_group)
            newNameWidget.setLayout(QtWidgets.QHBoxLayout())
            newNameWidget.layout().setAlignment(QtCore.Qt.AlignLeft)
            newNameWidget.layout().setContentsMargins(0,0,0,0)
            newNameWidget.layout().setSpacing(0)
            newNameWidget.setSizePolicy(QtWidgets.QSizePolicy.Ignored,QtWidgets.QSizePolicy.Preferred)
            self.newName = ElidedLabel(newNameWidget)
            self.newName.setFont(font)
            self.newName.setSizePolicy(QtWidgets.QSizePolicy.Preferred,QtWidgets.QSizePolicy.Preferred)
            self.newNameHidden = ElidedLabel(newNameWidget)
            self.newNameHidden.setFont(font2)
            self.newNameHidden.setMaximumWidth(50)
            self.newNameHidden.setEnabled(False)
            self.newNameHidden.setVisible(False)
            self.newNameHidden.setSizePolicy(QtWidgets.QSizePolicy.Fixed,QtWidgets.QSizePolicy.Preferred)
            newNameWidget.layout().addWidget(self.newNameHidden)
            newNameWidget.layout().addWidget(self.newName)
            self.ui.formLayout.setWidget(0,QtWidgets.QFormLayout.FieldRole,self.crtName)
            self.ui.formLayout.setWidget(1,QtWidgets.QFormLayout.FieldRole,newNameWidget)
            self.updateCrtLabel()
        
        def configPresets():
            presetDefault = [{'type':'Text','val1':'obj_'},{'type':'Sequence Number','val1':'1','format':'Four Digits'}]
            presetStrSub = [{'type':'String Substitution','val1':'','val2':'','format':'Original Name','opt1':False,'opt2':False,'opt3':False}]
            
            def setPreset(preset):
                presetCopied = copy.deepcopy(preset)
                for row in range(len(presetCopied)):
                    item = self.generatorList.item(row)
                    if item:
                        generator = self.generatorList.itemWidget(item)
                        generator.setSetting(presetCopied[row])
                    else:
                        generator = initGenerator()
                        generator.setSetting(presetCopied[row])
                if self.generatorList.count() > len(presetCopied):
                    for row in range(len(presetCopied),self.generatorList.count()):
                        item = self.generatorList.item(len(presetCopied))
                        removeGenerator(item)
            
            def resetModifiedPreset():
                self.ui.presetCombo.setItemData(0,QtCore.QSize(0,0),QtCore.Qt.SizeHintRole)
                self.modifiedPreset = ''
                self.ui.presetCombo.setItemText(0,self.modifiedPreset)
            
            def onPresetChanged():
                preset = self.ui.presetCombo.currentText()
                # Lock setting until finish loading
                self.settingLock = True
                
                if self.ui.presetCombo.currentIndex() == 0 and preset == self.modifiedPreset:
                    self.ui.presetCombo.model().item(0).setEnabled(True)
                    self.ui.deleteButton.setEnabled(False)
                else:
                    self.ui.presetCombo.model().item(0).setEnabled(False)
                    resetModifiedPreset()
                    # clearGeneratorList()
                    if preset == 'Last Used':
                        self.ui.deleteButton.setEnabled(False)
                        setting = os.path.abspath(os.path.join(self.settingDirectory,'!Last.setting'))
                        if os.path.exists(setting):
                            with open(setting) as f:
                                data = json.load(f)
                            data = data[1:]
                            setPreset(data)
                        else:
                            self.ui.presetCombo.setCurrentText('Default')
                    elif preset == 'Default':
                        self.ui.deleteButton.setEnabled(False)
                        setPreset(presetDefault)
                    elif preset == 'String Substitution':
                        self.ui.deleteButton.setEnabled(False)
                        setPreset(presetStrSub)
                    else:
                        self.ui.deleteButton.setEnabled(True)
                        setting = os.path.abspath(os.path.join(self.settingDirectory,preset+'.setting'))
                        if os.path.exists(setting):
                            with open(setting) as file:
                                data = json.load(file)
                            setPreset(data)
                        else:
                            msgBox = QtWidgets.QMessageBox.critical(self, "Error", "No such preset found", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
                            # Delete
                            index = self.ui.presetCombo.currentIndex()
                            self.ui.presetCombo.removeItem(index)
                            if index == 6:
                                self.ui.presetCombo.setCurrentIndex(index-2)
                            else:
                                self.ui.presetCombo.setCurrentIndex(index-1)
                    
                # Unlock setting
                self.settingLock = False
                self.updateNewLabel()
                    
            def onDeleteClicked():
                currentPreset = self.ui.presetCombo.currentText()
                msgBox = QtWidgets.QMessageBox.question(self, "Delete Preset", "Do you really want to delete {}?".format(currentPreset), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)
                if msgBox == QtWidgets.QMessageBox.Yes:
                    index = self.ui.presetCombo.currentIndex()
                    setting = os.path.abspath(os.path.join(self.settingDirectory,currentPreset+'.setting'))
                    if os.path.exists(setting):
                        os.remove(setting)
                    if index == 6:
                        self.ui.presetCombo.setCurrentIndex(index-2)
                    else:
                        self.ui.presetCombo.setCurrentIndex(index-1)
                    self.ui.presetCombo.removeItem(index)
                
            def sortCombo(list):
                temp = []
                row = 6
                while list.itemText(row) != '':
                    temp.append(list.itemText(row))
                    list.removeItem(row)
                    self.ui.presetCombo.setCurrentIndex(4)
                temp = sorted(temp, key=lambda x:x.lower())
                list.addItems(temp)
                
            def insertOrder(list,text):
                temp = []
                for row in range(6,list.count()):
                    temp.append(list.itemText(row))
                temp.append(text)
                temp = sorted(temp, key=lambda x:x.lower())
                index = temp.index(text)+6
                list.insertItem(index,text)
            
            def onSaveClicked():
            
                def onOkClicked():
                    
                    def findOver(list,index,text):
                        temp = list.itemText(index)
                        list.setItemText(index,'')
                        isExist = list.findText(text)
                        list.setItemText(index,temp)
                        return isExist
                    
                    def saveSetting(inputName):
                        setting = os.path.abspath(os.path.join(self.settingDirectory,inputName+'.setting'))
                        # If folder is not exist, create new one
                        if not os.path.exists(os.path.dirname(setting)):
                            os.makedirs(os.path.dirname(setting))
                        # Write file
                        with open(setting,'w') as file:
                            json.dump(self.crtSettings, file, indent=2)
                    
                    inputName = dialog.getInput()
                    isExist = findOver(self.ui.presetCombo,0,inputName)
                    # If preset is already exists, show overwrite dialog
                    if isExist >= 0:
                        if inputName in ['Last Used', 'Default', 'String Substitution']:
                            msgBox = QtWidgets.QMessageBox.critical(dialog, "Error", "Cannot replace preserved preset.", QtWidgets.QMessageBox.Ok, QtWidgets.QMessageBox.Ok)
                        else:
                            msgBox = QtWidgets.QMessageBox.question(dialog, "Confirm Replace", "{} already exists. Do you want to replace it?".format(inputName), QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)
                            if msgBox == QtWidgets.QMessageBox.Yes:
                                resetModifiedPreset()
                                saveSetting(inputName)
                                self.ui.presetCombo.setCurrentText(inputName)
                                dialog.close()
                    else:
                        resetModifiedPreset()
                        saveSetting(inputName)
                        insertOrder(self.ui.presetCombo,inputName)
                        self.ui.presetCombo.setCurrentText(inputName)
                        dialog.close()
                    
                dialog = saveDialog(self)
                dialog.setInput(self.ui.presetCombo.currentText())
                dialog.selectAll()
                dialog.show()
                dialog.buttonBox.accepted.connect(onOkClicked)
                dialog.buttonBox.rejected.connect(dialog.close)
                return dialog
                
            def createPresetList():
                # Initiate modified preset row and then hide it
                self.ui.presetCombo.insertItem(0,self.modifiedPreset)
                self.ui.presetCombo.model().item(0).setEnabled(False)
                self.ui.presetCombo.setItemData(0,QtCore.QSize(0,0),QtCore.Qt.SizeHintRole)
                self.ui.presetCombo.insertSeparator(1)
                
                # Add default preset
                self.ui.presetCombo.addItem('Last Used')
                self.ui.presetCombo.addItem('Default')
                self.ui.presetCombo.addItem('String Substitution')
                self.ui.presetCombo.insertSeparator(5)
                
                # Load presets from directory
                if os.path.exists(self.settingDirectory):
                    # Get all presets and add to combobox
                    settings = os.listdir(self.settingDirectory)
                    for setting in settings:
                        if setting.rpartition(".")[0] == '!Last': continue
                        if setting.rpartition(".")[2] == 'setting':
                            self.ui.presetCombo.addItem(setting.rpartition(".")[0])
                sortCombo(self.ui.presetCombo)

            def initPreset():
                lastSetting = os.path.abspath(os.path.join(self.settingDirectory,'!Last.setting'))
                if os.path.exists(lastSetting):
                    with open(lastSetting) as f:
                        data = json.load(f)
                    lastPreset = data[0]['preset']
                    state = data[0]['state']
                    # If preset is found then select preset and not a modified preset
                    if self.ui.presetCombo.findText(lastPreset) != -1 and state == 1:
                        self.ui.presetCombo.setCurrentText(lastPreset)
                        onPresetChanged()
                    # Else load as new modified preset
                    else:
                        self.modifiedPreset = lastPreset
                        self.ui.presetCombo.setItemText(0,self.modifiedPreset)
                        # Show modified preset row (row 0)
                        self.ui.presetCombo.setItemData(0,None,QtCore.Qt.SizeHintRole)
                        self.ui.presetCombo.setCurrentIndex(0)
                        
                        # Current index is already 0 so it will not trigger onPresetChanged.
                        # Therefore, we set it manually
                        self.ui.presetCombo.model().item(0).setEnabled(True)
                        self.ui.deleteButton.setEnabled(False)
                        data = data[1:]
                        self.settingLock = True
                        setPreset(data)
                        self.settingLock = False
                else:
                    self.ui.presetCombo.setCurrentText('Default')
            
            def connectInterface():
                self.ui.presetCombo.currentIndexChanged.connect(onPresetChanged)
                self.ui.deleteButton.clicked.connect(onDeleteClicked)
                self.ui.saveButton.clicked.connect(onSaveClicked)
                
            createPresetList()
            connectInterface()
            initPreset()
            self.updateNewLabel()
            
        def createGeneratorList():
            stylesheet = "QListWidget{\
                            background: transparent;\
                            border: none;\
                            outline: none;\
                          }\
                          QListWidget::item{\
                            background: transparent;\
                            border: none;\
                            color: black;\
                          }"
            self.generatorList = QtWidgets.QListWidget()
            self.generatorList.setFixedHeight(self.generatorList_height)
            self.generatorList.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
            self.generatorList.setStyleSheet(stylesheet)
            self.generatorList.setAcceptDrops(True)
            self.generatorList.setDragEnabled(True)
            self.generatorList.setDropIndicatorShown(True)
            self.generatorList.setDefaultDropAction(QtCore.Qt.MoveAction)
            # Signals and slots
            generatorList_model = self.generatorList.model()
            generatorList_model.rowsInserted.connect(onRowChanged)
            generatorList_model.rowsRemoved.connect(onRowChanged)
            generatorList_model.rowsMoved.connect(onRowChanged)
            # Add to main UI
            self.ui.newNames_group.layout().addWidget(self.generatorList)
            
        def clearGeneratorList():
            # Permanently delete all items
            self.generatorList.clear()
            self.generatorList_height = 0
            self.window_height = self.default_window_height
            self.setFixedHeight(self.window_height)
            self.generatorList.setFixedHeight(self.generatorList_height)
        
        def initGenerator():
            generator = generatorWidget()
            self.generatorDefaultHeight = generator.sizeHint().height()+self.generatorItemMargin
            item = QtWidgets.QListWidgetItem()
            item.setSizeHint(QtCore.QSize(0, self.generatorDefaultHeight))
            self.generatorList.addItem(item)
            generator.addButton.clicked.connect(partial(addGenerator,item))
            generator.removeButton.clicked.connect(partial(removeGenerator,item))
            generator.settingChanged.connect(partial(onSettingChanged,item))
            self.generatorList.setItemWidget(item, generator)
            updateUI(item,'+')
            # Initiated generator is not detected by signal, so we do it manually
            onRowChanged()
            return generator

        def addGenerator(item):
            self.settingLock = True
            generator = generatorWidget()
            generator.setSetting({'type':'Text','val1':''})
            row = self.generatorList.row(item)
            newItem = QtWidgets.QListWidgetItem()
            newItem.setSizeHint(QtCore.QSize(0, self.generatorDefaultHeight))
            self.generatorList.insertItem(row+1,newItem)
            generator.addButton.clicked.connect(partial(addGenerator,newItem))
            generator.removeButton.clicked.connect(partial(removeGenerator,newItem))
            generator.settingChanged.connect(partial(onSettingChanged,newItem))
            self.generatorList.setItemWidget(newItem, generator)
            self.settingLock = False
            updateUI(item,'+')
            return generator

        def removeGenerator(item):
            row = self.generatorList.row(item)
            updateUI(item,'-')
            item = self.generatorList.takeItem(row)
            item = None
            
        def updateUI(item,mode):
            if mode == '+':
                height = self.generatorDefaultHeight
                self.generatorList_height += height
                self.window_height += height
            elif mode == '-':
                row = self.generatorList.row(item)
                height = self.generatorList.item(row).sizeHint().height()
                self.generatorList_height -= height
                self.window_height -= height
            else:
                return
            self.generatorList.setFixedHeight(self.generatorList_height)
            self.setFixedHeight(self.window_height)
            
            if createModifiedPreset() != 1:
                self.updateNewLabel()
            
        def createModifiedPreset():
            # If settingLock is True, don't create modified preset
            if self.settingLock:
                return 1
            
            # Create modified preset
            if self.modifiedPreset == '':
                self.modifiedPreset = '{} (Modified)'.format(self.ui.presetCombo.currentText())
                self.ui.presetCombo.setItemText(0,self.modifiedPreset)
                # Show modified preset row (row 0)
                self.ui.presetCombo.setItemData(0,None,QtCore.Qt.SizeHintRole)
                self.ui.presetCombo.setCurrentIndex(0)
                return -1
            
        def onRowChanged():
            item = self.generatorList.item(0)
            firstGenerator = self.generatorList.itemWidget(item)
            if not firstGenerator:
                return
            if self.generatorList.count() == 1:
                firstGenerator.removeButton.setEnabled(False)
            else:
                firstGenerator.removeButton.setEnabled(True)
                
            if createModifiedPreset() != 1:
                self.updateNewLabel()
            
        def onSettingChanged(item,*args):
            type = args[0]['type']
            
            def updateItemSize(item,type):
                row = self.generatorList.row(item)
                crtHeight = self.generatorList.item(row).sizeHint().height()
                newHeight = self.generatorList.itemWidget(item).getSizeHint().height()+self.generatorItemMargin
                item.setSizeHint(QtCore.QSize(0,newHeight))
                height_diff = abs(newHeight - crtHeight)
                if type == 'String Substitution':
                    self.generatorList_height += height_diff
                    self.window_height += height_diff
                else:
                    self.generatorList_height -= height_diff
                    self.window_height -= height_diff
                self.generatorList.setFixedHeight(self.generatorList_height)
                self.setFixedHeight(self.window_height)
                
            updateItemSize(item,type)
            
            if createModifiedPreset() != 1:
                self.updateNewLabel()
            
        configLabel()
        createGeneratorList()
        configPresets()
    
    def updateCrtLabel(self):
        if self.selection:
            self.crtName.setEnabled(True)
            # When obj has duplicated name it will have | with parent name, so we'll get only the name
            shortName = self.selection[0].split('|')[-1]
            self.crtName.setText(shortName)
        else:
            self.crtName.setEnabled(False)
            self.crtName.setText('-')
            
    def updateNewLabel(self):
        self.getAllSettings()
        # for setting in self.crtSettings:
            # print setting
        if self.selection:
            self.newName.setEnabled(True)
            # shortName = self.selection[0].split('|')[-1]
            self.newName.setText(self.renames(self.selection[0])) # assign setting
        else:
            self.newName.setEnabled(False)
            self.newName.setText('-')
            
    def getAllSettings(self):
        # Get all settings in generatorList
        self.crtSettings = []
        for row in range(self.generatorList.count()):
            item = self.generatorList.item(row)
            setting = self.generatorList.itemWidget(item).getSetting()
            self.crtSettings.append(setting)
        
    def updateGuide(self):
        text = 'will be processed'
        count = len(self.selection)
        if count == 0: text = 'No objects '+text
        elif count == 1: text = 'One object '+text
        else: text = '{} objects '.format(count)+text
        self.ui.guideLabel.setText(text)
    
    def updateRenameButton(self):
        if not self.selection:
            self.ui.renameButton.setEnabled(False)
        else:
            self.ui.renameButton.setEnabled(True)
    
    def rename(self,obj,type,val1,val2,format,opt1,opt2,opt3,index,intm_name):
        
        def changeCase(crtName,format='Original Case'):
            if format == 'Original Case':
                newName = crtName
            elif format == 'UPPERCASE':
                newName = crtName.upper()
            elif format == 'lowercase':
                newName = crtName.lower()
            else:
                cmds.error('Format error')
            return newName
            
        def toNumber(character):
            number = ord(character.lower()) - 96
            return number
        
        def toCharacter(number):
            normalized_number = number % 26
            if normalized_number == 0: normalized_number = 26
            character = chr(ord('`') + normalized_number)
            return character
            
        if type == 'Text':
            newName = val1
        elif type == 'Current Object Name':
            shortName = obj.split('|')[-1]
            newName = changeCase(shortName,format)
        elif type == 'Current Object Type':
            objType = cmds.objectType(obj)
            if objType == 'transform':
                shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) # Return full path in case of object has duplicated name
                if shapes:
                    objType = cmds.objectType(shapes[0])
                else:
                    objType = 'group'
            newName = changeCase(objType,format)
        elif type == 'Parent Name':
            parents = cmds.listRelatives(parent=True)
            if parents:
                parent = parents[0]
            else:
                parent = ''
            newName = changeCase(parent,format)
        elif type == 'Sequence Number':
            val1 = int(val1)+index
            if format == 'One Digit':
                val1 = val1 % 10
                output = "%01d" % val1
            elif format == 'Two Digits':
                val1 = val1 % 100
                output = "%02d" % val1
            elif format == 'Three Digits':
                val1 = val1 % 1000
                output = "%03d" % val1
            elif format == 'Four Digits':
                val1 = val1 % 10000
                output = "%04d" % val1
            elif format == 'Five Digits':
                val1 = val1 % 100000
                output = "%05d" % val1
            elif format == 'Six Digits':
                val1 = val1 % 1000000
                output = "%06d" % val1
            else:
                cmds.error('Format error')
            newName = output
        elif type == 'Sequence Letter':
            char_number = toNumber(val1)+index
            char = toCharacter(char_number)
            newName = changeCase(char,format)
        elif type == 'String Substitution':
            #--------------------Format---------------------#
            if format == 'Original Name':
                shortName = obj.split('|')[-1]
                name = shortName
            elif format == 'Intermediate Name':
                name = intm_name
            else:
                cmds.error('Format error')
            #-----------------------------------------------#
            if val1 != '':
                flags = 0
                #--------------------Options--------------------#
                # Ignore Case
                if opt1: flags |= re.IGNORECASE
                # Replace All
                if opt2: maxreplace = 0
                else: maxreplace = 1
                # Use Regular Expression
                if opt3: regex = val1
                else: regex = re.escape(val1)
                #----------------------------------------------#
                pattern = re.compile(regex, flags=flags)
                newName = pattern.sub(val2, name, count=maxreplace)
            else:
                newName = name
        else:
            cmds.error('Type error')
        
        return newName
        
    def renames(self,obj,index=0):
        # Loop all settings
        newName = ''
        for setting in self.crtSettings:
            # Get setting
            type = setting.get('type', None)
            val1 = setting.get('val1', None)
            val2 = setting.get('val2', None)
            format = setting.get('format', None)
            opt1 = setting.get('opt1', None)
            opt2 = setting.get('opt2', None)
            opt3 = setting.get('opt3', None)
            intm_name = newName
            # Rename
            output = self.rename(obj,type,val1,val2,format,opt1,opt2,opt3,index,intm_name)
            # Generate new name
            if format == 'Intermediate Name':
                newName = output
            else:
                newName += output
            
        # If new name starts with number, delete it
        if newName and newName[0].isdigit():
            deletedNum = re.findall("\d*", newName)[0]
            newName = re.sub("\d*", "", newName, 1)
            # Show deleted number widget
            self.newNameHidden.setVisible(True)
            self.newNameHidden.setText(deletedNum)
        else:
            # Hide deleted number widget
            self.newNameHidden.setVisible(False)
            self.newNameHidden.setText('')
            
        if newName == '':
            self.ui.renameButton.setEnabled(False)
        else:
            self.ui.renameButton.setEnabled(True)
        return newName
        
    def renamesAll(self,sel,order,index=0):
        if not sel:
            return
        crt_sel = sel
        crt_order = order
        while crt_sel:
            obj = crt_sel.pop(0)
            obj_order = crt_order.pop(0)
            shortName = obj.split('|')[-1]
            crtName = shortName
            newName = self.renames(obj,obj_order)
            #--------------Handle duplicated name---------------#
            if self.isDuplicate(obj,newName) and crtName != newName:
                dup_index = self.duplicateIndex(crt_sel,obj,newName)
                if dup_index != -1: # If selection has duplicated name
                    dup_obj = crt_sel.pop(dup_index)
                    dup_order = crt_order.pop(dup_index)
                    crt_sel.insert(0,obj)
                    crt_order.insert(0,obj_order)
                    crt_sel.insert(0,dup_obj)
                    crt_order.insert(0,dup_order)
                    continue
                else:
                    count = 1
                    temp = '{}_{}'.format(newName,count)
                    while self.isDuplicate(obj,temp):
                        count += 1
                        temp = '{}_{}'.format(newName,count)
                    newName = temp
                    # newName += '_#'
            #-------------------------------------------------#
            # print obj,newName
            cmds.rename(obj,newName)
            index += 1
    
    def getNewNameFullPath(self,crtName,newName):
        try:
            parents = cmds.listRelatives(crtName,parent=True,fullPath=True)
            newName_fullPath = '{}|{}'.format(parents[0],newName)
        except:
            newName_fullPath = '|{}'.format(newName)
            
        return newName_fullPath
        
    def isDuplicate(self,crtName,newName):
        result = cmds.objExists(self.getNewNameFullPath(crtName,newName))
        return result
        
    def duplicateIndex(self,sel,crtName,newName):
        newName_fullPath = self.getNewNameFullPath(crtName,newName)
            
        for index,obj in enumerate(sel):
            if obj == newName_fullPath:
                break
        else:
            index = -1
        
        return index
    
    def onClickRename(self):
        try:
            cmds.undoInfo(openChunk=True)
            # Copy self.selection so we won't lose the original
            sel=sorted(self.selection,key=len, reverse=True)
            order = [i[0] for i in sorted(enumerate(self.selection), key=lambda tup: len(tup[1]), reverse=True)]
            # print 'SEL: {}'.format(sel)
            # print 'ORD: {}'.format(order)
            self.renamesAll(sel,order)
        # except:
            # cmds.error('An error occurred')
        finally:
            cmds.undoInfo(closeChunk=True)
            self.close()
    
    def onClickPreview(self):
        prev = previewDialog(self)
        # Reset
        prev.clear()
        
        # Add items
        for index,obj in enumerate(self.selection):
            shortName = obj.split('|')[-1]
            crtName = shortName
            newName = self.renames(obj,index)
            if crtName != newName:
                #--------------Handle duplicated name---------------#
                # if self.isDuplicate(crtName,newName) or prev.findItem(newName) != -1:
                    # count = 1
                    # temp = '{}_{}'.format(newName,count)
                    # while prev.findItem(temp) != -1: # If found
                        # count += 1
                        # temp = '{}_{}'.format(newName,count)
                    # newName = temp
                #-------------------------------------------------#
                prev.addItem(crtName,newName)
        # Update guide label
        prev.updateGuide()
        
        prev.show()
        return prev
        
    def onSelectionChanged(self):
        self.selection = cmds.ls(selection=True,objectsOnly=True,long=True)
        self.updateRenameButton()
        self.updateGuide()
        self.updateCrtLabel()
        self.updateNewLabel()
    
    def closeEvent(self,event):
        # super(batchRenameUI,self).closeEvent(event)
        # Save last setting before closing
        settings = []
        index = self.ui.presetCombo.currentIndex()
        if index == 0: state = 0
        else: state = 1
        settings.append({'preset':self.ui.presetCombo.currentText(),'state':state})
        settings.extend(self.crtSettings)
            
        lastSetting = os.path.abspath(os.path.join(self.settingDirectory,'!Last.setting'))
        # If folder is not exist, create new one
        if not os.path.exists(os.path.dirname(lastSetting)):
            os.makedirs(os.path.dirname(lastSetting))
        # Write file
        with open(lastSetting,'w') as file:
            json.dump(settings, file, indent=2)
            
        # Save window's geometry
        settings_obj = QtCore.QSettings(self.settings_path, QtCore.QSettings.IniFormat)
        settings_obj.setValue("batchRename_windowGeometry", self.saveGeometry())
            
        # Kill script job
        if cmds.scriptJob(exists=self.SCRIPT_JOB_NUMBER): cmds.scriptJob(kill=self.SCRIPT_JOB_NUMBER, force=True)
        
    def keyPressEvent(self,event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        
    def connectInterface(self):
        self.ui.renameButton.clicked.connect(self.onClickRename)
        self.ui.cancelButton.clicked.connect(self.close)
        self.ui.previewButton.clicked.connect(self.onClickPreview)

def execute():
    ui = batchRenameUI()
    ui.show()
    return ui

def main():
    execute()
    
if __name__ == "__main__":
    main()
