"""
Created on 04.07.2017

@author: Matthias Hensen

Converts the input spatial reference name to a string which is used as
parameter item by the function arcpy.SpatialReference(item).

function: convert_spatial_reference(spatial_reference)

"""

import logging

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def convert_spatial_reference(spatial_reference):
    """Convert input data GPSpatialReference to arcpy.item.name.
    
    The input parameter spatial_reference type GPSpatialReference 
    cannot be used to create a spatial_reference with arcpy. This 
    function converts the input to a string name of the item spatial
    reference. The item could be used as parameter by the function
    arcpy.SpatialReference(item).
    
    @param spatial_reference (GPSpatialReference): 
        The input Spatial reference.
    
    @return spatial reference(GPString): 
        The name of the item.
    
    """
    
    try:
        logger.debug("Start converting of " + spatial_reference + ".") 
        spatial_reference = spatial_reference.split("',", 1)
        logger.debug("Split string: " + str(spatial_reference[0]) + ".")
        spatial_reference = str(spatial_reference[0])
        spatial_reference = spatial_reference.split("['", 1)
        logger.debug("Split string: " + str(spatial_reference[1]) + ".")
        spatial_reference = str(spatial_reference[1])
        spatial_reference = spatial_reference.replace("_", " ")
        logger.debug("Replace '_' by whitespace.")
        logger.info("Converting of spatial_reference completed.")
        return spatial_reference
    except (TypeError, IndexError, ValueError, AttributeError) as e: 
        logger.error(e + " while converting. Set value to epsg:25832.")
        return 25832