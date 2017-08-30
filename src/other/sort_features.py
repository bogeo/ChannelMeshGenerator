"""
Created on 14.07.2017

@author: Matthias Hensen

Sort features and save these in a same-named feature class.

function: sort_features(in_features, sort_field)
"""

import logging

import arcpy

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def sort_features(in_features, sort_fields):
    """Sort features and save these in a same-named feature class.
    
    Sorts a feature class by one or more field and returns them in a
    feature class with the same name as the input name.
    
    @param in_features (DEFeatureClass): 
        The feature class with the features which should be sorted.
    @param sort_fields (list): 
        The sort field and the sort direction.
    
    @return in_features (DEFeatureClass): 
        The sorted feature class.
    
    """
    logger.debug("Create 'temp_features'.")
    temp_features = "temp_features"
    arcpy.CopyFeatures_management(in_features, temp_features)
    logger.debug("'temp_features' created successfully.")
    
    logger.debug("Delete input feature class.")
    arcpy.Delete_management(in_features)
    logger.debug("Input feature class deleted successfully.")
    
    logger.debug("Sort " + str(sort_fields) + ".")
    arcpy.Sort_management(temp_features, in_features, sort_fields)
    logger.debug("Sorting features finished successfully.")
    
    logger.debug("Delete 'temp_features'.")
    arcpy.Delete_management(temp_features)
    logger.debug("'temp_features' deleted successfully.")
    
    return in_features