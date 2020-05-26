# T1 & ECV Mapping


# Introduction 

T1 & ECV Mapping is an extension of [3D Slicer Software](https://www.slicer.org/) that takes advantage of the physical properties of the Look Locker (LL) sequence to find the cardiac T1 Mapping. When the Native and late contrast-enhanced (Enhanced) T1 Mapping are created and the hematocrit value is known, the module allows the creation of the Extracellular Volume (ECV) map. T1 & ECV Mapping can be used to monitor fibrotic tissue since it provides four views in which the user can simultaneously see the Native and late contrast-enhanced T1 mapping, the ECV map and the viability sequence.
 
# Functionality

The module is divided, by collapsible buttons, in four sections. 
* **Input Volumes**: In this section the user must select the Native and Enhanced Look Locker. After that, by clicking the "Create T1 Mapping" button, the module will calculate both, the Native and the Enhanced T1 Mapping. There is also a button called "Refresh views" which sets the recommended volumes to the slice view, and a check button, called "Fix Scalar Volume', which blocks and automatically sets the inputs for the sections of the module. 

* **Statistics**: In this section the user will be able to assess the statistics for some region of interests that can be done with the [Segment Editor module](https://slicer.readthedocs.io/en/latest/user_guide/module_segmenteditor.html). Unless the check button is "checked", the statistics will be evaluated on the scalar volumes selected in this section. If it is checked the module will show the results for the same ROI in both, Native and Enhanced T1 Mapping. 

* **ECV Map**: In this section, if the check button is "unchecked", the user will have to select the Native and Enhanced T1 mapping to create the ECV map. It is also necessary to enter the Hematocrit percentage and the T1 values of the blood for both mappings. To do it automatically the user should create only one ROI in the cavity and then compute the statistics.

* **Threshold Controllers**: This section allows to manage the threshold in the Native, Enhanced and ECV mappings.

 # Install instructions
 
 T1 & ECV Mapping is currently distributed as an extension via the 3D Slicer ExtensionManager. To use this extension download the version 4.11 and above of [3D Slicer](https://download.slicer.org/) and follow the instructions detailed in [Extension manager](https://www.slicer.org/wiki/Documentation/4.3/SlicerApplication/ExtensionsManager). When the module is installed you will be able to find it going to the module list and looking in the Quantification section.

# Where to start

To start, it is recommended to the user to acquire the Native and Enhanced Look Locker for Trigger times in the intervals [100,3000] ms and [50,1300] ms respectively. Moreover, it is necessary that the sequences have the same geometries in order to be able to create the ECV map. With the images acquired, the user must upload the Look Locker Dicom files to the slicer as explained in [Dicom module](https://www.slicer.org/wiki/Documentation/Nightly/Modules/DICOM). At this point the user will be ready to start using the module. 

 
 # Tutorial
 
To illustrate how to use this module we created the next tutorial video. Try to follow the steps in the tutorial in your computer downloading the [Sample Data](https://github.com/RivettiLuciano/SlicerT1_ECVMapping/releases/download/v1.0/Sample1.zip).

[![IMAGE ALT TEXT HERE](https://github.com/RivettiLuciano/SlicerT1_ECVMapping/blob/master/Screen%20shots/Mappings.png)](https://www.youtube.com/watch?v=MRO2bF7bIDY)


 
 # Acknowledgments

This work was funded by Fundación Escuela de Medicina Nuclear ([FUESMEN](https://www.fuesmen.edu.ar/)) and Fundación Argentina para el Desarrollo en Salud (FADESA).

# Slicer Version

This module is available for Slicer 4.11 and above.


# References

1. [Method used to calculate the T1 Mapping](https://pubmed.ncbi.nlm.nih.gov/15236377/)

# License

This Module is in agreement with the [Slicer License](https://github.com/Slicer/Slicer/blob/master/License.txt) 
