# T1 & ECV Mapping


# Introduction 

T1 & ECV Mapping is an extension of [3D Slicer Software](https://www.slicer.org/) that takes advantage of the physical properties of the Look Locker (LL) sequence to find the cardiac T1 Mapping. When the Native and late contrast-enhanced (Enhanced) T1 Mapping are created and the hematocrit value is known, the module allows the creation of the Extracellular Volume (ECV) map. T1 & ECV Mapping can be used to monitor fibrotic tissue since it provides four views in which the user can simultaneously see the Native and late contrast-enhanced T1 mapping, the ECV map and the viability sequence.
 
# Functionality

The module is divided, by collapsible buttons, in four sections. 
* **Input Volumes**: In this section the user must to select the Native and Ehanced Look Locker. After that, clicking the "Create T1 Mapping" button, the module will calculate both, the Native and the Enhanced T1 Mapping. There is also a button called "Refresh views" which sets the recommended volumes to the slice view, and a check button, called "Fix Scalar Volume', which blocks and automatically sets the inputs for the Statistics and ECV section. 

* **Statistics**: In this section the user will be able assess the stadistics of some region of interes that the user can make with the [Segment Editor module](https://slicer.readthedocs.io/en/latest/user_guide/module_segmenteditor.html). The stadistics will be evaluated on the scalar volumes selected. If the check button is "checked" the module will compute the statistics for the same ROI in both, Native and Enhanced T1 Mapping. 

* **ECV Map**: In this section, if the check button is "unchecked", the user will have to select the Native and Enhanced T1 mapping to create the ECV map. It is also necessary to write the percentage of Hematocrit and the T1 values of the blood for both mappings. To do it atomatically the user can create only one ROI in the cavitity and the use the Statistics secction.

* **Threshold Controllers**: This section allows to manage the threshold in the Native, Enhanced and ECV mappings.


# Where to start

To start, it is recommended to the user to acquire the Native-LL for Trigger times in the interval [100,3000] ms and the Enhanced-LL for Trigger times in the interval [50,1300] ms. Moreover, it is necessary that the Look Locker sequences have the same geometries in order to be able to create the ECV map. With the images acquired, the user must to upload the Dicom files of the look locker sequences to the slicer as explained in [Dicom module](https://www.slicer.org/wiki/Documentation/Nightly/Modules/DICOM). At this point the user will be ready to start using the module. 

 # Install instructions
 
 T1 & ECV Mapping is currently distributed as an extension via the 3D Slicer ExtensionManager. To use this extension download the latest version of [3D Slicer](https://download.slicer.org/) and follow the instructions detailed in [Extension manager](https://www.slicer.org/wiki/Documentation/4.3/SlicerApplication/ExtensionsManager). When the module is installed you will be able to find it if you go to the module list and look for in the Quantification section.
 
 # Tutorial
 
To illustrate how to use this module we created the next tutorial video.

[![IMAGE ALT TEXT HERE](https://github.com/RivettiLuciano/SlicerT1_ECVMapping/blob/master/Screen%20shots/Mappings.png)](https://www.youtube.com/watch?v=MRO2bF7bIDY)

You can do it in your computer. Download the [Dicom examples](https://github.com/RivettiLuciano/SlicerT1_ECVMapping/tree/master/Dicom%20Examples) and copy the steps in the tutorial.
 
 # Acknowledgments

This work was funded by Fundación Escuela de Medicina Nuclear ([FUESMEN](https://www.fuesmen.edu.ar/)) and Fundación Argentina para el Desarrollo en Salud (FADESA).



# References

1. [Method used to calculate the T1 Mapping](https://pubmed.ncbi.nlm.nih.gov/15236377/)

# License

This Module is in agreement with the [Slicer License](https://github.com/Slicer/Slicer/blob/master/License.txt) 
