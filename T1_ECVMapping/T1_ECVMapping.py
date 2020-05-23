import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import numpy as np
from scipy.optimize import curve_fit
import pydicom
import slicer
import DataProbeLib
import SegmentStatistics
from scipy import interpolate
#
# T1_ECVMapping
#

class T1_ECVMapping(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "T1 & ECV Mapping"  
    self.parent.categories = ["Quantification"]  
    self.parent.dependencies = []  
    self.parent.contributors = ["Luciano Rivetti, Daniel Fino, Marcela Niela"]  
    self.parent.helpText = """
This module takes advantage of the properties of the Look Locker sequence to calculate the Native and Post-contrast cardiac T1 Mapping. This also allows the creation
of the ECV Map using both Mappings.
"""  
    self.parent.helpText += self.getDefaultModuleDocumentationLink()  
    self.parent.acknowledgementText = """
This work was funded by Fundación Escuela de Medicina Nuclear (FUESMEN) and Fundación Argentina para el Desarrollo en Salud (FADESA).
Module implemented by Luciano Rivetti. Based on the method described by (Messroghli et al., 2004).
"""  # TODO: replace with organization, grant and thanks.

#
# T1_ECVMappingWidget
#

class T1_ECVMappingWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None
    self.T1_LLN_Node = None
    self.T1_LLE_Node = None
    self.ECVMapNode = None
    self.LLE_Node = None
    self.LLN_Node = None
    self.ArefNode = None
    self.T1_LLE_Name = 'T1 Enhanced'
    self.T1_LLN_Name = 'T1 Native'
    self.ResetSliceViews()
    self.LinkSlices()
    self.ColorBarEnabled()
    self.setupVolumeNodeViewLayout()
    self.Warning = True

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)
    self.reloadCollapsibleButton.collapsed   = True
    # Instantiate and connect widgets ...
    #
    
    # Inputs volume selectors
    DataCollButtom = ctk.ctkCollapsibleButton()
    DataCollButtom.text = "Input Volumes"
    self.layout.addWidget(DataCollButtom)
    self.InputOutput_Layout = qt.QFormLayout(DataCollButtom)
    self.setupAnatomicalRef()
    self.setupLL_Native()
    self.setupLL_Enhanced()

    # Apply Buttons
    self.setRefreshViewsAndCheckButtonButton()
    self.setT1Button()

    # Statistics section widgets
    Statistics = ctk.ctkCollapsibleButton()
    Statistics.text = "Statistics"
    Statistics.collapsed = True
    self.layout.addWidget(Statistics)
    self.Statistics_Layout = qt.QFormLayout(Statistics)
    self.Stats = statistics()
    self.Stats.setupSegmentationSelector(self.Statistics_Layout,self.layout)

    # ECV section widgets
    ECVcollButton = ctk.ctkCollapsibleButton()
    ECVcollButton.text = "ECV Mapping"
    ECVcollButton.collapsed = True
    self.layout.addWidget(ECVcollButton)
    self.ECVcollButton_Layout = qt.QFormLayout(ECVcollButton)
    self.setECVScalarVolume()
    self.setupSpinBoxControllers()
    self.setECVButton()

    # Threshold Controllers 
    ThCollButton = ctk.ctkCollapsibleButton()
    ThCollButton.text = "Threshold controlers"
    ThCollButton.collapsed = True
    self.layout.addWidget(ThCollButton)
    self.Th_Layout = qt.QFormLayout(ThCollButton)
    self.ThSlider_LLN = DoubleSlider(self.Th_Layout, self.SetThreshold)
    self.ThSlider_LLN.SetupDoubleSliderControl(WidgetName = 'T1-Native Threshold')
    self.ThSlider_LLE = DoubleSlider(self.Th_Layout, self.SetThreshold)
    self.ThSlider_LLE.SetupDoubleSliderControl(WidgetName = 'T1-Enhanced Threshold')
    self.ThSlider_ECV = DoubleSlider(self.Th_Layout, self.SetThreshold)
    self.ThSlider_ECV.SetupDoubleSliderControl(WidgetName = 'ECV Mapping')

    self.onCheckbuttonChecked()
    self.setupConnections()


  
  def setupLL_Enhanced(self):
    """ Set up the Scalar Volume Selector for the Enhanced Look Locker"""
    self.LLE_Selector = slicer.qMRMLNodeComboBox()
    self.LLE_Selector.nodeTypes = ['vtkMRMLMultiVolumeNode']
    self.LLE_Selector.noneEnabled = True
    self.LLE_Selector.setMRMLScene(slicer.mrmlScene)
    self.LLE_Selector.addEnabled = 0
    self.LLE_SelectorLabel = qt.QLabel('Enhanced Look Locker')
    self.LLE_Selector.setToolTip("Select the post contrast Look Locker to create the T1 Mapping")
    self.InputOutput_Layout.addRow(self.LLE_SelectorLabel, self.LLE_Selector)
    


  def setupLL_Native(self):
    """ Set up the Scalar Volume Selector for the Native Look Locker"""
    self.LLN_Selector = slicer.qMRMLNodeComboBox()
    self.LLN_Selector.nodeTypes = ['vtkMRMLMultiVolumeNode']
    self.LLN_Selector.noneEnabled = True
    self.LLN_Selector.setMRMLScene(slicer.mrmlScene)
    self.LLN_Selector.addEnabled = 0
    self.LLN_SelectorLabel = qt.QLabel('Native Look Locker')
    self.LLN_Selector.setToolTip("Select the pre contrast Look Locker to create the T1 Mapping")
    self.InputOutput_Layout.addRow(self.LLN_SelectorLabel, self.LLN_Selector)

  def setupAnatomicalRef(self):
    """ Set up the Scalar Volume Selector for the Anatomical Reference"""
    self.Aref_Selector = slicer.qMRMLNodeComboBox()
    self.Aref_Selector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    self.Aref_Selector.noneEnabled = True
    self.Aref_Selector.setMRMLScene(slicer.mrmlScene)
    self.Aref_Selector.addEnabled = 0
    self.Aref_SelectorLabel = qt.QLabel('Anatomical Reference')
    self.Aref_SelectorLabel.setToolTip("Select the Anatomical sequence to visualize")
    self.InputOutput_Layout.addRow(self.Aref_SelectorLabel, self.Aref_Selector)

  def setT1Button(self):
    """ Set up the apply button which create the T1 Mapping"""
    self.T1Button = qt.QPushButton("Create T1 Mapping")
    self.T1Button.toolTip = "Create the T1 Mapping of the Scalar Volumes selected"
    self.T1Button.enabled = False
    self.InputOutput_Layout.addRow(self.T1Button)
     
  def setRefreshViewsAndCheckButtonButton(self):
    """ Set up the apply button which refresh the slicer views. It also create a check button to fix the scalar volumes"""
    self.RViewButton = qt.QPushButton("Refresh views")
    self.RViewButton.toolTip = "Refresh the slice views"
    self.RViewButton.enabled = True

    self.CheckButton = qt.QCheckBox('Fix Scalar Volumes')
    self.CheckButton.toolTip = "Automatically block and set the selected volumes as the imputs for the statistics and ECV part of the module"
    self.CheckButton.setChecked(True)

    HLayout = qt.QHBoxLayout()
    HLayout.addWidget(self.RViewButton)
    HLayout.addWidget(self.CheckButton)

    self.InputOutput_Layout.addRow(HLayout)

  def setupSpinBoxControllers (self):
    """ Set up the spin box controllers to calculate the ECV map """
    self.SB_NBlodd_Label = qt.QLabel('Native T1 Blood')
    self.SB_EBlodd_Label = qt.QLabel('Enhanced T1 Blood')
    self.SB_Haematocrit_Label = qt.QLabel('Haematocrit Percentage')
    self.SB_Haematocrit = qt.QDoubleSpinBox()
    self.SB_NBlodd = qt.QDoubleSpinBox()
    self.SB_EBlodd = qt.QDoubleSpinBox()
    self.ConfigSpinBox(self.SB_Haematocrit,self.SB_Haematocrit_Label,1,0,100, Suffix='%')
    self.ConfigSpinBox(self.SB_NBlodd,self.SB_NBlodd_Label,1,0,2000)
    self.ConfigSpinBox(self.SB_EBlodd,self.SB_EBlodd_Label,1,0,1000)


  def ConfigSpinBox(self,SpinBox,Name,Step,Min,Max,Suffix=''):
    """ Set up the Spin box characteristics """
    HLayout = qt.QHBoxLayout()
    HLayout.addWidget(Name)
    HLayout.addWidget(SpinBox)
    self.ECVcollButton_Layout.addRow(HLayout)
    SpinBox.setSingleStep(Step)
    SpinBox.setRange(Min,Max)
    SpinBox.suffix = Suffix

  def setECVScalarVolume (self):
    """ Set up the scalar volume selector for the Native and Enhanced T1 mapping """
    self.NativeT1_Selector = slicer.qMRMLNodeComboBox()
    self.NativeT1_Selector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    self.NativeT1_Selector.noneEnabled = True
    self.NativeT1_Selector.setMRMLScene(slicer.mrmlScene)
    self.NativeT1_Selector.addEnabled = 0
    self.NativeT1_Selector_Label = qt.QLabel('Native T1 Mapping')
    self.NativeT1_Selector.setToolTip("Select the Native T1 Mapping to create the ECV map")
    self.ECVcollButton_Layout.addRow(self.NativeT1_Selector_Label, self.NativeT1_Selector)

    self.EnhancedT1_Selector = slicer.qMRMLNodeComboBox()
    self.EnhancedT1_Selector.nodeTypes = ['vtkMRMLScalarVolumeNode']
    self.EnhancedT1_Selector.noneEnabled = True
    self.EnhancedT1_Selector.setMRMLScene(slicer.mrmlScene)
    self.EnhancedT1_Selector.addEnabled = 0
    self.EnhancedT1_Selector_Label = qt.QLabel('Enhanced T1 Mapping')
    self.EnhancedT1_Selector.setToolTip("Select the Enhanced T1 Mapping to create the ECV map")
    self.ECVcollButton_Layout.addRow(self.EnhancedT1_Selector_Label, self.EnhancedT1_Selector)

  def setECVButton(self):
    """ Set up the apply button which create the ECV map """
    self.ECVButton = qt.QPushButton("Create ECV Map")
    self.ECVButton.toolTip = "Create the ECV map with the volumes selected as Native and Enhanced LL"
    self.ECVButton.enabled = False
    self.ECVcollButton_Layout.addRow(self.ECVButton)
  
  def setupConnections(self):
    """ Set up the connections of all the widgets created before """
    self.T1Button.connect('clicked(bool)', self.onApplyButton)
    self.RViewButton.connect('clicked(bool)', self.onApplyRViewButton)
    self.CheckButton.connect('stateChanged(int)', self.onCheckbuttonChecked)
    self.LLE_Selector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelectLLENode)
    self.LLN_Selector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelectLLNNode)
    self.Aref_Selector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelectArefNode)

    self.ThSlider_LLE.Slider.connect("positionsChanged(double,double)",self.ThSlider_LLE.onSliderChanged)
    self.ThSlider_LLE.SpinBoxL.connect("valueChanged(int)", self.ThSlider_LLE.onSpinBoxLChanged)
    self.ThSlider_LLE.SpinBoxR.connect("valueChanged(int)", self.ThSlider_LLE.onSpinBoxRChanged)
    
    self.ThSlider_LLN.Slider.connect("positionsChanged(double,double)",self.ThSlider_LLN.onSliderChanged)
    self.ThSlider_LLN.SpinBoxL.connect("valueChanged(int)", self.ThSlider_LLN.onSpinBoxLChanged)
    self.ThSlider_LLN.SpinBoxR.connect("valueChanged(int)", self.ThSlider_LLN.onSpinBoxRChanged)    

    self.ThSlider_ECV.Slider.connect("positionsChanged(double,double)",self.ThSlider_ECV.onSliderChanged)
    self.ThSlider_ECV.SpinBoxL.connect("valueChanged(int)", self.ThSlider_ECV.onSpinBoxLChanged)
    self.ThSlider_ECV.SpinBoxR.connect("valueChanged(int)", self.ThSlider_ECV.onSpinBoxRChanged)
  
    self.Stats.segmentationSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.Stats.onScalarSelectorChanged)
    self.Stats.scalarSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.Stats.onScalarSelectorChanged)
    self.Stats.scalarSelector2.connect("currentNodeChanged(vtkMRMLNode*)", self.Stats.onScalarSelector2Changed)
    self.Stats.SButton.connect('clicked(bool)', self.onApplyGetStatistics)

    self.NativeT1_Selector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelectNT1Node)
    self.EnhancedT1_Selector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelectET1Node)
    self.SB_NBlodd.connect("valueChanged(Double)", self.onSpinBoxNBChanged)
    self.SB_EBlodd.connect("valueChanged(Double)", self.onSpinBoxEBChanged)
    self.SB_Haematocrit.connect("valueChanged(Double)", self.onSpinBoxHChanged)
    self.ECVButton.connect('clicked(bool)',self.onApplyECVButton)
      
  
  def ResetSliceViews(self):
    """ Set all the views in None"""
    num = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSliceCompositeNode')
    for i in range(num):
        sliceViewer = slicer.mrmlScene.GetNthNodeByClass(i, 'vtkMRMLSliceCompositeNode')
        sliceViewer.SetBackgroundVolumeID(None)
        sliceViewer.SetForegroundVolumeID(None)


  def SetThreshold (self,VolumeNode, min, max):
    """ Set the minimum and maximum threshold values of a Node"""
    DisplayNode = VolumeNode.GetScalarVolumeDisplayNode()
    DisplayNode.SetApplyThreshold(True)
    DisplayNode.SetThreshold(min,max)


  def ColorBarEnabled(self):
    """ it Makes appear the scalar bar for the background volumes"""
    sliceAnnotations = DataProbeLib.SliceAnnotations()
    sliceAnnotations.scalarBarEnabled = 1
    sliceAnnotations.updateSliceViewFromGUI()    


  def onSelectLLNNode(self):
    """ It makes all the configurations needed when the LLN node changes"""
    self.T1Button.enabled = self.LLE_Selector.currentNode() or self.LLN_Selector.currentNode()
    self.LLN_Node = self.LLN_Selector.currentNode()
    if not self.LLN_Node:
      self.ThSlider_LLN.SetNode(None) 
      self.updateThresholdValues(self.ThSlider_LLN,self.LLN_Node,0)
      self.SetLayoutViewer(None, 'Green') 
      self.onCheckbuttonChecked()
      return  
    Labels = T1_ECVMappingLogic.getMultiVolumeLabels(self,self.LLN_Node)
    if (np.min(Labels) > 150 or np.max(Labels) < 2400) and self.Warning :
      slicer.util.warningDisplay('The trigger time interval is not the recommended to get a good T1 Mapping. Try to make a Native LL in the interval [100,3000] ms', windowTitle= 'Warning')
    try :
      self.T1_LLN_Node = slicer.util.getNode(self.T1_LLN_Name)
      self.ThSlider_LLN.SetNode(self.T1_LLN_Node) 
      self.onCheckbuttonChecked()
      if self.T1_LLN_Node.GetImageData() == None:
        return
      self.T1_LLN_Array = slicer.util.arrayFromVolume(self.T1_LLN_Node)
      max = np.nanmax(self.T1_LLN_Array)
      self.updateThresholdValues(self.ThSlider_LLN, self.T1_LLN_Node, max)
      self.SetLayoutViewer(self.T1_LLN_Node, 'Green')    
    except:
      self.T1_LLN_Node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode', self.T1_LLN_Name)
      self.updateThresholdValues(self.ThSlider_LLN,self.LLN_Node,0)
      self.onCheckbuttonChecked()


  def onSelectLLENode(self):
    """ It makes all the configurations needed when the LLE node changes"""
    self.T1Button.enabled = self.LLE_Selector.currentNode() or self.LLN_Selector.currentNode()
    self.LLE_Node = self.LLE_Selector.currentNode()
    if not self.LLE_Node:
      self.ThSlider_LLE.SetNode(None) 
      self.updateThresholdValues(self.ThSlider_LLE,self.LLE_Node,0)
      self.SetLayoutViewer(None, 'Yellow') 
      self.onCheckbuttonChecked()
      return  
    Labels = T1_ECVMappingLogic.getMultiVolumeLabels(self,self.LLE_Node)
    if (np.min(Labels) > 115 or np.max(Labels) < 800) and self.Warning:
      slicer.util.warningDisplay('The trigger time interval is not the recommended to get a good T1 Mapping. Try to make a Native LL in the interval [50,1300] ms', windowTitle= 'Warning')
    try :
      self.T1_LLE_Node = slicer.util.getNode(self.T1_LLE_Name)
      self.ThSlider_LLE.SetNode(self.T1_LLE_Node) 
      self.onCheckbuttonChecked()
      if self.T1_LLE_Node.GetImageData() == None:
        return
      self.T1_LLE_Array = slicer.util.arrayFromVolume(self.T1_LLE_Node)
      max = np.nanmax(self.T1_LLE_Array)
      self.updateThresholdValues(self.ThSlider_LLE, self.T1_LLE_Node, max)
      self.SetLayoutViewer(self.T1_LLE_Node, 'Yellow')
    except:
      self.T1_LLE_Node = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode', self.T1_LLE_Name)
      self.updateThresholdValues(self.ThSlider_LLE,self.LLE_Node,0)
      self.onCheckbuttonChecked()



  def onSelectArefNode(self):
    """ It makes all the configurations needed when the Aref node changes"""
    self.ArefNode = self.Aref_Selector.currentNode()
    if not self.ArefNode:
      self.SetLayoutViewer(None, 'Red')
      return  
    self.SetLayoutViewer(self.ArefNode, 'Red')


  def SetLayoutViewer (self, Node, sliceViewName):
    """ Set the image of the Node in the view sliceViewName"""
    SliceCompositeName = 'vtkMRMLSliceCompositeNode' + sliceViewName
    slicerViewer = slicer.mrmlScene.GetNodeByID(SliceCompositeName)
    slicerViewer.SetForegroundVolumeID(None)
    if not Node or Node.GetImageData()==None:
      slicerViewer.SetBackgroundVolumeID(None)
      return
    slicerViewer.SetBackgroundVolumeID(Node.GetID())
    self.RotateSliceView(Node, sliceViewName)
    slicer.util.resetSliceViews()


  def RotateSliceView (self, Node, sliceViewName):
    """ Rotates the slice in order to see whole image"""
    volNode = Node
    sliceNode = slicer.app.layoutManager().sliceWidget(sliceViewName).mrmlSliceNode()
    sliceToRas = sliceNode.GetSliceToRAS()
    VtkMatrix = vtk.vtkMatrix4x4()
    volNode.GetIJKToRASMatrix(VtkMatrix)
    M = np.zeros((4,4))   #### IJK To RAS Numpy Matrix 
    for i in range (4):
        for j in range (4):
            M[i,j] = VtkMatrix.GetElement(i,j)

    Dim = volNode.GetImageData().GetDimensions()
    t = M.dot(np.array([(Dim[0]-1)/2,(Dim[1]-1)/2,0,1]))
    for i in range (4):
        VtkMatrix.SetElement(i,3,t[i])
        VtkMatrix.SetElement(i,2,VtkMatrix.GetElement(i,2)/-10) 
        VtkMatrix.SetElement(i,1,VtkMatrix.GetElement(i,1)*-1) # The minus sign, above and here, is a Pi rotation around the X axis.

    sliceToRas.DeepCopy(VtkMatrix)
    sliceNode.UpdateMatrices()
    sliceNode.RotateToVolumePlane(volNode)    


  def LinkSlices(self):
    """ Link all the Slice views  """
    sliceCompositeNodes = slicer.util.getNodesByClass('vtkMRMLSliceCompositeNode')
    defaultSliceCompositeNode = slicer.mrmlScene.GetDefaultNodeByClass('vtkMRMLSliceCompositeNode')
    if not defaultSliceCompositeNode:
      defaultSliceCompositeNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLSliceCompositeNode')
      slicer.mrmlScene.AddDefaultNode(defaultSliceCompositeNode)
    sliceCompositeNodes.append(defaultSliceCompositeNode)
    for sliceCompositeNode in sliceCompositeNodes:
      sliceCompositeNode.SetLinkedControl(True)

    
  def updateThresholdValues (self, DoubleSlider, Node, ThMax ):
    """ From the scalar volume update the threshold values of the Doubleslider and Spin box """
    DoubleSlider.Slider.minimum = 0
    DoubleSlider.SpinBoxL.setRange(0,ThMax)
    DoubleSlider.Slider.maximum = ThMax
    DoubleSlider.SpinBoxR.setRange(0,ThMax)
    if ThMax!=0:
      DisplayNode = Node.GetScalarVolumeDisplayNode()
      LowerThreshold = DisplayNode.GetLowerThreshold()
      UpperThreshold = DisplayNode.GetUpperThreshold()
      DoubleSlider.Slider.minimumValue = LowerThreshold
      DoubleSlider.Slider.maximumValue = UpperThreshold 
      DoubleSlider.SpinBoxL.blockSignals(True)
      DoubleSlider.SpinBoxR.blockSignals(True)
      DoubleSlider.SpinBoxL.value = LowerThreshold
      DoubleSlider.SpinBoxR.value = UpperThreshold
      DoubleSlider.SpinBoxL.blockSignals(False)
      DoubleSlider.SpinBoxR.blockSignals(False)


  def onApplyButton(self):
    import time

    self.T1Button.setText('Processing ...') 
    self.T1Button.enabled = False    

    if not slicer.util.confirmYesNoDisplay('It could take a few minutes. Do you want to run it anyway?'):
      self.T1Button.enabled = True
      self.T1Button.setText('Create T1 Mapping') 
      return

    self.T1Button.enabled = True
    self.T1Button.setText('Create T1 Mapping') 

    self.Warning = False
    self.onApplyRViewButton()
    self.LinkSlices()
    time_start = time.time()
    logic_Native = T1_ECVMappingLogic('Native')
    logic_Native.run(self.LLN_Node , self.T1_LLN_Node)
    self.SetScalarDisplay(self.T1_LLN_Node, MinThresh = 100)
    self.onSelectLLNNode()
    logic_Enhanced = T1_ECVMappingLogic('Enhanced')
    logic_Enhanced.run(self.LLE_Node , self.T1_LLE_Node)
    self.SetScalarDisplay(self.T1_LLE_Node)
    self.onSelectLLENode()
    print('Running Time = ',time.time()-time_start)
    self.setupVolumeNodeViewLayout()
    self.Warning = True


  def onApplyRViewButton(self):
  
    self.SetLayoutViewer(self.ArefNode,'Red')
    self.SetLayoutViewer(self.T1_LLN_Node,'Green')
    self.SetLayoutViewer(self.T1_LLE_Node,'Yellow') 
    try:
      self.ECVMapNode = slicer.util.getNode('ECV Map')
    except:
      pass
    self.SetLayoutViewer(self.ECVMapNode,'Slice4')
    self.setupVolumeNodeViewLayout()
    self.LinkSlices()
    

  def onCheckbuttonChecked(self):  
    """ Block the user to select the scalar volumes in the ECV and Statistics part of the program """
    if self.CheckButton.isChecked() == True:
       if not self.LLN_Node:
        self.Stats.scalarSelector.setCurrentNode(None)
        self.NativeT1_Selector.setCurrentNode(None)   
        self.Stats.scalarSelector.enabled = False
        self.NativeT1_Selector.enabled = False
       else:
        self.Stats.scalarSelector.setCurrentNode(self.T1_LLN_Node)
        self.NativeT1_Selector.setCurrentNode(self.T1_LLN_Node)
        self.Stats.scalarSelector.enabled = False
        self.NativeT1_Selector.enabled = False
       if self.LLE_Node:
        self.Stats.scalarSelector2.setCurrentNode(self.T1_LLE_Node)
        self.EnhancedT1_Selector.setCurrentNode(self.T1_LLE_Node)
        self.Stats.scalarSelector2.enabled = False
        self.EnhancedT1_Selector.enabled = False        
       else:
        self.Stats.scalarSelector2.setCurrentNode(None)
        self.EnhancedT1_Selector.setCurrentNode(None)      
        self.Stats.scalarSelector2.enabled = False
        self.EnhancedT1_Selector.enabled = False                 
    else:
        self.Stats.scalarSelector.setCurrentNode(None)
        self.Stats.scalarSelector2.setCurrentNode(None)
        self.NativeT1_Selector.setCurrentNode(None)
        self.EnhancedT1_Selector.setCurrentNode(None)
        self.Stats.scalarSelector.enabled = True
        self.NativeT1_Selector.enabled = True
        self.Stats.scalarSelector2.enabled = True
        self.EnhancedT1_Selector.enabled = True             


  def setupVolumeNodeViewLayout(self):
    """ Configurate the View Layout"""
    layoutNodes = slicer.mrmlScene.GetNodesByClass('vtkMRMLLayoutNode')
    layoutNodes.SetReferenceCount(layoutNodes.GetReferenceCount()-1)
    layoutNodes.InitTraversal()
    layoutNode = layoutNodes.GetNextItemAsObject()
    layoutNode.SetViewArrangement(slicer.vtkMRMLLayoutNode.SlicerLayoutTwoOverTwoView)

  def SetScalarDisplay(self, ScalarvolumeNode, MinThresh = 10, Max = False):
    """ Configurate the display nodes"""
    if not ScalarvolumeNode or ScalarvolumeNode.GetScalarVolumeDisplayNode()==None:
      return
    SvD = ScalarvolumeNode.GetScalarVolumeDisplayNode()
    SvD.SetAndObserveColorNodeID('vtkMRMLColorTableNodeRainbow')
    SvD.SetAutoWindowLevel(True)
    SvD.SetApplyThreshold(True)
    MaxThresh = SvD.GetUpperThreshold()
    if Max:
      MaxThresh = Max
    SvD.SetThreshold(MinThresh, MaxThresh)   

  def onApplyGetStatistics (self):
    self.Stats.onApplySButton()
    mean = self.Stats.ROImean
    if len(mean)==2:
      self.SB_NBlodd.value = max(mean)
      self.SB_EBlodd.value = min(mean)



  def onSelectNT1Node (self):
    self.ECVButton.enabled = self.NativeT1_Selector.currentNode() and self.EnhancedT1_Selector.currentNode()

  def onSelectET1Node (self):
    self.ECVButton.enabled = self.NativeT1_Selector.currentNode() and self.EnhancedT1_Selector.currentNode()

  def onSpinBoxNBChanged(self, Value):
    self.SB_NBlodd.value = Value

  def onSpinBoxEBChanged(self, Value):
    self.SB_EBlodd.value = Value

  def onSpinBoxHChanged(self, Value):
    self.SB_Haematocrit.value = Value

  def onApplyECVButton(self):
    """ Create and configurate the ECV map """

    NodeName = 'ECV Map'
    try :
      self.ECVMapNode = slicer.util.getNode(NodeName)
    except:
      slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode', NodeName)
    self.ECVMapNode = slicer.util.getNode(NodeName)

    T1Native_Matrix,T1Enhanced_Matrix = self.MatchMatrixs(self.NativeT1_Selector.currentNode(),self.EnhancedT1_Selector.currentNode())

    Haematocrit = self.SB_Haematocrit.value
    NT1B = self.SB_NBlodd.value
    ET1B = self.SB_EBlodd.value
    Factor = (100-Haematocrit)*(NT1B*ET1B/(NT1B-ET1B))
    epsilon = 0.1

    T1Enhanced_Matrix = T1Enhanced_Matrix + epsilon
    T1Native_Matrix = T1Native_Matrix + epsilon
    self.ECV_Matrix = (1/T1Enhanced_Matrix-1/T1Native_Matrix)*Factor
    self.ECV_Matrix = np.nan_to_num(self.ECV_Matrix)
    self.ECV_Matrix[ np.logical_or(self.ECV_Matrix<0 , self.ECV_Matrix>100) ] = 0

    slicer.util.updateVolumeFromArray(self.ECVMapNode, self.ECV_Matrix)
    self.SetLayoutViewer(self.ECVMapNode, 'Slice4')
    self.SetScalarDisplay(self.ECVMapNode, 1, 100) ## Que onda el Auto WL
    self.ThSlider_ECV.SetNode(self.ECVMapNode)
    Max = np.nanmax(self.ECV_Matrix)
    self.updateThresholdValues(self.ThSlider_ECV, self.ECVMapNode, Max)



  def MatchMatrixs (self,Node1,Node2):
    """ This tries to match the T1 Native and Enhanced image matrix if they haven't the same number of pixels"""

    T1Native_Node = Node1
    T1Native_Matrix = slicer.util.arrayFromVolume(T1Native_Node)
    DimN = T1Native_Matrix.shape
    T1Enhanced_Node = Node2
    T1Enhanced_Matrix = slicer.util.arrayFromVolume(T1Enhanced_Node)
    DimE = T1Enhanced_Matrix.shape

    NMatrix = self.GetIJKToRASnpArray(T1Native_Node)
    NVector = NMatrix[:-1,-1]
    EMatrix = self.GetIJKToRASnpArray(T1Enhanced_Node)
    EVector = EMatrix[:-1,-1]
    NPixelSize = [np.linalg.norm(NMatrix[:-1,0]), np.linalg.norm(NMatrix[:-1,1])]
    EPixelSize = [np.linalg.norm(EMatrix[:-1,0]), np.linalg.norm(EMatrix[:-1,1])]

    Niversor = NMatrix[:-1,0]/NPixelSize[0]
    Njversor = NMatrix[:-1,1]/NPixelSize[1]
    Nkversor = np.round(np.cross(Niversor,Njversor),3)
    Nkstep = round(np.linalg.norm(NMatrix[:-1,2]),3)

    Eiversor = EMatrix[:-1,0]/EPixelSize[0]
    Ejversor = EMatrix[:-1,1]/EPixelSize[1]
    Ekversor = np.round(np.cross(Eiversor,Ejversor),3)
    Ekstep = round(np.linalg.norm(EMatrix[:-1,2]),3)
    print(Nkversor,Ekversor,Nkstep,Ekstep,NVector,EVector,(NVector-EVector).dot(Ekversor))
    if not ( np.sum(Nkversor==Ekversor) == 3 and Nkstep==Ekstep and ((NVector-EVector).dot(Ekversor)) == 0 ): # it verifies if the slices are oriented in the same direction, with the same step between slices and if the first images are complanar.
      slicer.util.warningDisplay('The geometry of the LL Native and LL Enhanced volume doesn\'t match. It could deteriorate the ECV map', windowTitle= 'Warning')

    if (DimE == DimN):
      T1_ECVMappingLogic.setupNodeFromNode(self,self.ECVMapNode , self.NativeT1_Selector.currentNode()) 
      return [T1Native_Matrix,T1Enhanced_Matrix]
    if (DimE[1:3] == DimN[1:3]):
      k = min([DimE[1],DimN[1]])
      T1_ECVMappingLogic.setupNodeFromNode(self,self.ECVMapNode , self.NativeT1_Selector.currentNode())
      return [T1Native_Matrix[:k,:,:],T1Enhanced_Matrix[:k,:,:]]

    jN = np.arange(0,DimN[2]*NPixelSize[1],NPixelSize[1])+NPixelSize[1]/2+(NVector-EVector).dot(Njversor)
    iN = np.arange(0,DimN[1]*NPixelSize[0],NPixelSize[0])+NPixelSize[0]/2+(NVector-EVector).dot(Niversor)
    iE = np.arange(0,DimE[1]*EPixelSize[0],EPixelSize[0])+EPixelSize[0]/2
    jE = np.arange(0,DimE[2]*EPixelSize[1],EPixelSize[1])+EPixelSize[1]/2 
    if DimE[1] > DimN[1]:  ## I concidered a square image
      T1Nreshaped = np.zeros(DimE)
      for k in range(DimN[0]):
        f = interpolate.interp2d(iN, jN, np.nan_to_num(T1Native_Matrix[k,:,:]), fill_value = 0)
        T1Nreshaped[k,:,:] = f(iE, jE)
      T1Ereshaped = T1Enhanced_Matrix[:k+1,:,:]
      T1_ECVMappingLogic.setupNodeFromNode(self,self.ECVMapNode , self.EnhancedT1_Selector.currentNode())
      return [T1Nreshaped,T1Ereshaped]
    else:
      T1Ereshaped = np.zeros(DimN)
      for k in range(DimE[0]):
        f = interpolate.interp2d(iE, jE, np.nan_to_num(T1Enhanced_Matrix[k,:,:]), fill_value = 0)
        T1Ereshaped[k,:,:] = f(iN, jN)     
      T1Nreshaped = T1Native_Matrix[:k+1,:,:]
      T1_ECVMappingLogic.setupNodeFromNode(self,self.ECVMapNode , self.NativeT1_Selector.currentNode()) 
      return [T1Nreshaped,T1Ereshaped]
      

  def GetIJKToRASnpArray (self,Node):
    VtkMatrix = vtk.vtkMatrix4x4()
    Node.GetIJKToRASMatrix(VtkMatrix)
    M = np.zeros((4,4))
    for i in range (4):
      for j in range (4):
        M[i,j] = VtkMatrix.GetElement(i,j)
    return M


class DoubleSlider():
  """ This class creates and links a Double slider widget with two Spin Box """

  def __init__ (self, Display_Layout, function):
    self.function = function
    self.DisplayLayout = Display_Layout

  def SetNode(self,VolumeNode):
    self.VolumeNode = VolumeNode

  def SetupDoubleSliderControl(self, WidgetName= 'Set Threshold', SpinBoxStep = 5 ):
    self.Slider = ctk.ctkDoubleRangeSlider()
    self.Label = qt.QLabel(WidgetName)
    self.Slider.orientation = 1

    self.SpinBoxL = qt.QSpinBox()
    self.SpinBoxL.prefix = 'Min: '
    self.SpinBoxL.setSingleStep(SpinBoxStep)

    self.SpinBoxR = qt.QSpinBox()
    self.SpinBoxR.prefix = 'Max: '
    self.SpinBoxR.setSingleStep(SpinBoxStep)

    ControlHBox = qt.QHBoxLayout()
    ControlHBox.addWidget(self.Label)
    ControlHBox.addWidget(self.SpinBoxL)
    ControlHBox.addWidget(self.Slider)
    ControlHBox.addWidget(self.SpinBoxR)
    self.DisplayLayout.addRow(ControlHBox)

    self.Slider.minimum = 0
    self.SpinBoxL.setRange(0,0)

    self.Slider.maximum = 0
    self.SpinBoxR.setRange(0,0)

  def UpdateSpinBox(self,SpinBoxLNewValue, SpinBoxRNewValue):
    self.SpinBoxL.value = SpinBoxLNewValue
    self.SpinBoxR.value = SpinBoxRNewValue
    self.SpinBoxL.maximum = SpinBoxRNewValue
    self.SpinBoxR.minimum = SpinBoxLNewValue
     
  def onSliderChanged(self, SliderMin, SliderMax):
    if self.VolumeNode is None:
      return    
    self.UpdateSpinBox (SliderMin,SliderMax)
    self.function(self.VolumeNode,SliderMin, SliderMax)

  def onSpinBoxLChanged(self, Value):
    if self.VolumeNode is None:
      return 
    self.Slider.minimumValue = Value
    self.SpinBoxR.minimum = Value
    self.function(self.VolumeNode,Value,self.SpinBoxR.value)
    
  def onSpinBoxRChanged(self, Value):
    if self.VolumeNode is None:
      return 
    self.Slider.maximumValue = Value
    self.SpinBoxL.maximum = Value
    self.function(self.VolumeNode,self.SpinBoxL.value,Value)

  def SetWindowLabel(self, min, max):
    DisplayNode = self.VolumeNode.GetScalarVolumeDisplayNode()
    DisplayNode.SetAutoWindowLevel(False)
    Window = max-min
    Label = (max+min)/2
    DisplayNode.SetWindowLevel(Window,Label)


  


class statistics():

  """ This class creates the statistics widgets and assess the Statistics of the scalar volumes selected """

  def setupSegmentationSelector(self,Layout,parent):
    self.segmentationSelector = slicer.qMRMLNodeComboBox()
    self.segmentationSelector.nodeTypes = ["vtkMRMLSegmentationNode"]
    self.segmentationSelector.addEnabled = False
    self.segmentationSelector.removeEnabled = True
    self.segmentationSelector.renameEnabled = True
    self.segmentationSelector.setMRMLScene( slicer.mrmlScene )
    self.segmentationSelector.setToolTip( "Pick the segmentation to compute statistics for" )
    Layout.addRow("Segmentation:", self.segmentationSelector)

    self.scalarSelector = slicer.qMRMLNodeComboBox()
    self.scalarSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.scalarSelector.addEnabled = False
    self.scalarSelector.removeEnabled = True
    self.scalarSelector.renameEnabled = True
    self.scalarSelector.noneEnabled = True
    self.scalarSelector.showChildNodeTypes = False
    self.scalarSelector.setMRMLScene( slicer.mrmlScene )
    self.scalarSelector.setToolTip( "Select the scalar volume that you want to get the statistics")
    Layout.addRow("Scalar Volume 1:", self.scalarSelector)

    self.scalarSelector2 = slicer.qMRMLNodeComboBox()
    self.scalarSelector2.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.scalarSelector2.addEnabled = False
    self.scalarSelector2.removeEnabled = True
    self.scalarSelector2.renameEnabled = True
    self.scalarSelector2.noneEnabled = True
    self.scalarSelector2.showChildNodeTypes = False
    self.scalarSelector2.setMRMLScene( slicer.mrmlScene )
    self.scalarSelector2.setToolTip( "Select the scalar volume that you want to get the statistics")
    Layout.addRow("Scalar Volume 2:", self.scalarSelector2)

    self.SButton = qt.QPushButton("Get Statistics")
    self.SButton.toolTip = "Get the statistics for the segmentation selected"
    self.SButton.enabled = False
    Layout.addRow(self.SButton)

    self.table = qt.QTableView()
    self.table.sortingEnabled = True
    parent.addWidget(self.table)


  def onSegmentationSelectorChanged(self):
    self.SButton.enabled = (self.scalarSelector2.currentNode() and self.segmentationSelector.currentNode()) or (self.scalarSelector.currentNode() and self.segmentationSelector.currentNode())

  def onScalarSelectorChanged(self):
    self.SButton.enabled = (self.scalarSelector2.currentNode() and self.segmentationSelector.currentNode()) or (self.scalarSelector.currentNode() and self.segmentationSelector.currentNode())

  def onScalarSelector2Changed(self):
    self.SButton.enabled = (self.scalarSelector2.currentNode() and self.segmentationSelector.currentNode()) or (self.scalarSelector.currentNode() and self.segmentationSelector.currentNode())

  def onApplySButton(self):
    """ This function takes advantage of the functions of the Segment Statistics module to assess the statistics of the segmentation"""
    self.stats = {}
    self.NofV = 1
    self.logic = SegmentStatistics.SegmentStatisticsLogic()
    self.parameterNode = self.logic.getParameterNode()
    self.parameterNode.SetParameter("Segmentation", self.segmentationSelector.currentNode().GetID())
    self.parameterNode.SetParameter('ClosedSurfaceSegmentStatisticsPlugin.enabled','False')
    self.parameterNode.SetParameter('LabelmapSegmentStatisticsPlugin.enabled','True')
    self.parameterNode.SetParameter('LabelmapSegmentStatisticsPlugin.volume_cm3.enabled','False')
    self.parameterNode.SetParameter('LabelmapSegmentStatisticsPlugin.volume_mm3.enabled','False')
    self.parameterNode.SetParameter('LabelmapSegmentStatisticsPlugin.voxel_count.enabled','False')
    self.parameterNode.SetParameter('LabelmapSegmentStatisticsPlugin.surface_area_mm2.enabled','True')

    if self.scalarSelector.currentNode():
      self.parameterNode.SetParameter("ScalarVolume", self.scalarSelector.currentNode().GetID())
      self.GetStats(self.scalarSelector.currentNode())

    if self.scalarSelector2.currentNode():
      self.parameterNode.SetParameter("ScalarVolume", self.scalarSelector2.currentNode().GetID())
      self.GetStats(self.scalarSelector2.currentNode())

    try:
      self.ROImean = np.array(self.stats['Mean'])
    except:
      self.ROImean = [0]

    self.PopulateTableStats()


  def GetStats(self,Node):
    self.logic.computeStatistics()
    keys = self.logic.getNonEmptyKeys()
    longname, names = self.logic.getHeaderNames(keys)
    self.statistics = self.logic.getStatistics()
    Stats = {}
    for key in keys:
      measurements = [self.statistics[segmentID, key] for segmentID in self.statistics["SegmentIDs"] if
                      (segmentID, key) in self.statistics] 
      Stats[names[key]] = measurements

    if 'Mean [1]' in Stats.keys():
      Stats['Minimum'] = Stats.pop('Minimum [1]')
      Stats['Maximum'] = Stats.pop('Maximum [1]')
      Stats['Mean'] = Stats.pop('Mean [1]')
      Stats['Median'] = Stats.pop('Median [1]')
      Stats['Standard Deviation'] = Stats.pop('Standard Deviation [1]')

    Stats['Scalar Volume'] = [Node.GetName()]*len(Stats['Segment'])

    if not bool(self.stats):
      self.stats = Stats
    else:
      for k in self.stats.keys():
        self.stats[k].extend(Stats[k])
        self.NofV = 2

  def PopulateTableStats(self):
    """ Creates the Qt table with the statistics"""

    NewOrderKeys = ['Segment','Scalar Volume','Mean','Standard Deviation', 'Minimum','Maximum', 'Median','Number of voxels [voxels]','Surface area [mm2]','Volume [mm3]','Volume [mm3]' ]
    self.items = []
    self.model = qt.QStandardItemModel()
    self.table.setModel(self.model)
    self.table.verticalHeader().visible = False
    segmentationNode = self.segmentationSelector.currentNode()
    row = 0
    NofSegments = len(self.statistics['SegmentIDs'])
    I = np.concatenate((np.arange(NofSegments),np.arange(NofSegments)))

    for i in range(len(list(self.stats.values())[0])):
      col = 0
      color = qt.QColor() 
      segment = segmentationNode.GetSegmentation().GetSegment(self.statistics['SegmentIDs'][I[i]]) 
      rgb = segment.GetColor()
      color.setRgb(rgb[0]*255,rgb[1]*255,rgb[2]*255)
      item = qt.QStandardItem()
      item.setData(color,qt.Qt.DecorationRole)
      item.setEditable(False)
      self.model.setItem(row,col,item)
      self.items.append(item)
      col += 1
      for k in NewOrderKeys:
        item = qt.QStandardItem()
        item.setData(self.stats[k][i],qt.Qt.DisplayRole)
        item.setEditable(False)
        self.model.setItem(row,col,item)
        self.items.append(item)
        col += 1
      row += 1

    col = 0
    self.table.setColumnWidth(0,30)
    self.model.setHeaderData(0,1," ")
    col += 1

    for k in NewOrderKeys:
      self.table.setColumnWidth(col,16*len(k))
      self.model.setHeaderData(col,1,k)
      col += 1



#
# T1_ECVMappingLogic
#

class T1_ECVMappingLogic(ScriptedLoadableModuleLogic):

  def __init__ (self, mode):
    self.mode = mode

  def getMultiVolumeLabels(self,volumeNode):
    """ Get the Trigger time of the volumeNode"""

    frameLabels = volumeNode.GetAttribute('MultiVolume.FrameLabels')
    nFrames = volumeNode.GetNumberOfFrames()
    mvLabels = [0,]*nFrames
    if frameLabels:
      mvLabels = frameLabels.split(',')
      if len(mvLabels) == nFrames:
        for l in range(nFrames):
          mvLabels[l] = float(mvLabels[l])
    else:
      for l in range(nFrames):
        mvLabels[l] = float(l)
    return mvLabels


  def Signal(self,x,A,B,Ts,c):
      return np.abs(A-B*np.exp(-x/Ts))+c

  def TsToT1 (self,A,B,Ts):
      return Ts*(B/A-1)

  def SigmaT1(self,A,B,Ts,DeltaT,cov):  ## It is the error of T1 taking into account that Signal is np.abs(A-B*np.exp(-(TrgTime+DeltaT)/Ts)) 
      dT1_dTs = B*np.exp(DeltaT/Ts)/A*(1-DeltaT/Ts)
      dT1_dB = Ts*np.exp(DeltaT/Ts)/A
      dT1_dA = -Ts*np.exp(DeltaT/Ts)*B/A**2
      return np.sqrt(np.abs(dT1_dA**2*cov[0,0]+dT1_dB**2*cov[1,1]+dT1_dTs**2*cov[2,2]+2*dT1_dA*dT1_dB*cov[0,1]+2*dT1_dA*dT1_dTs*cov[0,2]+2*dT1_dTs*dT1_dB*cov[1,2]+cov[2,2]))

  def GetDicomFromNode(self,node):
    """ Get Dicom Tags from a MRML node """
    storageNode=node.GetStorageNode()
    if storageNode is not None: # loaded via drag-drop
        filepath=storageNode.GetFullNameFromFileName()
    else: # loaded via DICOM browser
        instanceUIDs=node.GetAttribute('DICOM.instanceUIDs').split()
        filepath=slicer.dicomDatabase.fileForInstance(instanceUIDs[0])
    Dcm_tag=pydicom.dcmread(filepath)
    return Dcm_tag

  def FilterNoneValues(self, Matrix, dim, Value = False):
    """ Replace the None values of the T1 Mapping with the median value of the neighbors of the None pixels """
    kmax,imax,jmax = Matrix.shape
    Neighbor = dim//2
    for k in range (kmax):
      I,J = np.where(np.isnan(Matrix[k, :, :])) # change the shape of image in order to not have problems with the borders
      Conditional=np.logical_and(np.logical_and(imax-Neighbor>I, Neighbor<=I), np.logical_and(jmax-Neighbor>J, Neighbor <=J))
      I= I[Conditional]
      J= J[Conditional]
      Matrix_Filtered = np.copy(Matrix)
      for i in range (len(I)):
          M = Matrix[k,I[i]-Neighbor:I[i]+Neighbor+1,J[i]-Neighbor:J[i]+Neighbor+1]
          M=M[np.invert(np.isnan(M))]
          if len(M)>0 and Value==False:
              Matrix_Filtered[k,I[i],J[i]]=np.median(M)
          else :
              Matrix_Filtered[k,I[i],J[i]] = Value     
    return Matrix_Filtered

  def setupNodeFromNode(self, ScalarvolumeNode, MultivolumeNode):
    """ Copy the IJKToRASMatrix of the LL node to the new Scalar volume node"""
    ScalarvolumeNode.CreateDefaultDisplayNodes()
    ijkToRas = vtk.vtkMatrix4x4()
    MultivolumeNode.GetIJKToRASMatrix(ijkToRas)
    ScalarvolumeNode.SetIJKToRASMatrix(ijkToRas)

  def FitSignal(self,TT,S_ij,DeltaT,k):
    """ Try different seeds to fit the Signal function """
    Min = 40
    Max = 3000
    if self.mode == 'Enhanced':
      T1o = [300,200,250,400,500]
    if self.mode == 'Native':
     T1o = [1000,1500,650,1250,500]

    if k>=len(T1o):  
      return None
      
    Ao = np.max(S_ij)
    Bo=2*Ao
    Seed= [Ao,Bo,T1o[k]/(Bo/Ao-1),0]   
    try:
        [A,B,Ts,c],cov = curve_fit(self.Signal,TT,S_ij,Seed)
        T1 = self.TsToT1(A,B*np.exp(DeltaT/Ts),Ts)
      # dT1 = self.SigmaT1(A,B,Ts,DeltaT,cov)
        if  Min<T1<Max:
            return T1
        else:
           return self.FitSignal(TT,S_ij,DeltaT,k+1) 
    except:
          return self.FitSignal(TT,S_ij,DeltaT,k+1) 


  def run(self, MultivolumeNode, ScalarvolumeNode):
    if not MultivolumeNode:
      return

    TT=np.array(self.getMultiVolumeLabels(MultivolumeNode))
    Dcm = self.GetDicomFromNode(MultivolumeNode)   
    try:
        DeltaT = Dcm.InversionTime-Dcm.TriggerTime
    except:
        DeltaT = 0

    MvImg = slicer.util.arrayFromVolume(MultivolumeNode) 
    self.T1_Mapping = np.zeros(MvImg.shape[0:-1])

    for k in range(MvImg.shape[0]):
      mx = np.max(MvImg[k,:,:,:])/10
      I,J = np.where(MvImg[k,:,:,-1]>mx)
      for i in range (len(I)):
          S_ij=MvImg[k,I[i],J[i],:]
          self.T1_Mapping[k,I[i],J[i]] = self.FitSignal(TT,S_ij,DeltaT,0)     

    self.setupNodeFromNode(ScalarvolumeNode, MultivolumeNode)
    self.T1_Mapping_Filtered = self.FilterNoneValues(self.T1_Mapping,3)
    slicer.util.updateVolumeFromArray(ScalarvolumeNode,self.T1_Mapping_Filtered)


  def GetT1MappingError (self, MultivolumeNode, ScalarvolumeNode):
    """ This creates a node with an image which has high values in the pixels where in fitting did bad """
    NewNodeName = ScalarvolumeNode.GetName()+'+ Error'
    try :
      self.NewNode = slicer.util.getNode(NewNodeName)
    except:
      slicer.mrmlScene.AddNewNodeByClass('vtkMRMLScalarVolumeNode', NewNodeName)

    self.NewNode = slicer.util.getNode(NewNodeName)
    self.setupNodeFromNode(self.NewNode , MultivolumeNode)
    T1_MappingError = self.FilterNoneValues(self.T1_Mapping,3,10000)
    slicer.util.updateVolumeFromArray(self.NewNode,T1_MappingError)




class T1_ECVMappingTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Currently no testing functionality.
    """
    self.setUp()
    self.test_SegmentEditor1()

  def test_SegmentEditor1(self):
    """Add test here later.
    """
    self.delayDisplay("Starting the test")
    self.delayDisplay('Test passed!')
