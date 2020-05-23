cmake_minimum_required(VERSION 3.13.4)

project(T1_ECVMapping)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/RivettiLuciano/SlicerT1_ECVMapping")
set(EXTENSION_CATEGORY "Cardiac")
set(EXTENSION_CONTRIBUTORS "Luciano Rivetti (FUESMEN), Daniel Fino (FUESMEN-FADESA), Marcela Niela (FUESMEN-FADESA)")
set(EXTENSION_DESCRIPTION "This module takes advantage of the properties of the Look Locker sequence to calculate the Native and Post-contrast cardiac T1 Mapping. This also allows the creation of the ECV Map using both Mappings.")
set(EXTENSION_ICONURL "https://raw.github.com/RivettiLuciano/SlicerT1_ECVMapping/master/T1_ECVMapping.png")
set(EXTENSION_SCREENSHOTURLS "https://github.com/RivettiLuciano/SlicerT1_ECVMapping/blob/master/Screen%20shots/Module%20panel.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(T1_ECVMapping)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
