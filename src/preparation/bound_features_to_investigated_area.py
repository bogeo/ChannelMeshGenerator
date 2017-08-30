"""
Created on 13.07.2017

@author: Matthias Hensen

Bound the input features to the investigated area.

function: bound_features_to_investigated_area(workspace,
    adjusting_features, bounding_features, cutting_features,
    out_features_name, keep_names)
    
function: create_bounding_features(in_cross_sections)

function: create_cutting_features(in_cross_sections)
                
"""

import logging
import sys
import time

import arcpy

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def bound_features_to_investigated_area(
        workspace, adjusting_features, bounding_features, cutting_features,
        out_features_name, keep_names):
    """Bound the input features to the investigated area.
    
    The tool arcpy.FeatureToLine_management() splits the adjusting
    features and the bounding features at their intersections. The
    features which are not intersecting the cutting features are 
    selected and deleted. The bounded features are saved in an output
    feature class.
    
    @param workspace(DEWorkspace): 
        The workspace for results.
    @param adjusting_features(DEFeatureClass): 
        The feature class with the adjusting features.
    @param bounding_features(DEFeatureClass): 
        The feature class with the bounding features.
    @param cutting_features(List): 
        List with feature classes with the cutting features.
    @param out_features_name(GPString): 
        The output feature class name.
    @param keep_names(GPBoolean): 
        Input name = output name?
    
    @return out_features(DEFeatureClass): 
        The bounded features
    
    """
    logger.debug(
        "Split adjusting and bounding features at their intersections."
        )
    in_features = [adjusting_features, bounding_features]
    temp_features = "temp_features"
    arcpy.FeatureToLine_management(in_features, temp_features)
    logger.info("Splitting features finished successfully.")
    
    logger.debug("Create feature layer 'temp_layer'.")
    temp_layer = "temp_layer"
    arcpy.MakeFeatureLayer_management(temp_features, temp_layer)
    logger.info("Creating feature layer 'temp_layer' finished successfully.")

    logger.debug(
        "Select features which do not intersect " + cutting_features[0] + "."
        )
    overlap_type = "INTERSECT"
    search_distance = ""
    selection_type = "NEW_SELECTION"
    invert_spatial_relationship = "INVERT"
    arcpy.SelectLayerByLocation_management(
        temp_layer, overlap_type, cutting_features[0], search_distance,
        selection_type, invert_spatial_relationship)
    logger.info(
        "Features which do not intersect the cutting features selected "
        "successfully."
        )

    logger.debug("Delete this features.")
    arcpy.DeleteFeatures_management(temp_layer)
    logger.info("Deleting this features finished successfully.")
    
    if len(cutting_features) == 2:
        logger.debug(
            "Select features which do not intersect " + cutting_features[1] 
            + "."
            )
        arcpy.SelectLayerByLocation_management(
            temp_layer, overlap_type, cutting_features[1], search_distance,
            selection_type, invert_spatial_relationship)
        logger.info(
            "Features which do not intersect the cutting features selected "
            "successfully."
            )
        
        logger.debug("Delete this features.")
        arcpy.DeleteFeatures_management(temp_layer)
        logger.info("Deleting this features finished successfully.")

    logger.debug("Create output feature class.")
    if keep_names:
        out_features = adjusting_features
        arcpy.CopyFeatures_management(temp_layer, out_features)
        logger.info(
            "Output feature class " + out_features + " created successfully."
            )
    else:
        try:
            out_features = workspace + "/" + out_features_name
            arcpy.CopyFeatures_management(temp_layer, out_features)
            logger.info(
                "Output feature class " + out_features + " created "
                "successfully."
                )
        except arcpy.ExecuteError:
            logger.warning(
                out_features + " already exists. Change output name: " 
                + out_features + time.strftime("%d%m%y_%H%M%S.")
                )
            out_features = out_features + time.strftime("%d%m%y_%H%M%S")
            arcpy.CopyFeatures_management(temp_layer, out_features)
            logger.info(
                "Output feature class " + out_features + " created "
                "successfully."
                )
    
    logger.debug("Delete 'temp_layer' and 'temp_features'.")
    arcpy.Delete_management(temp_layer)
    arcpy.Delete_management(temp_features)
    logger.info("'temp_layer' and 'temp_features' deleted successfully.")
    
    return out_features


def create_bounding_features(in_cross_sections):
    """Create bounding features with the outer cross sections.
    
    With a cursor the outer cross sections are selected. These are saved
    in an output feature class.
    
    @param in_cross_sections(DEFeatureClass):
        The feature class with the input cross sections.
    
    @return out_bounding_features(DEFeatureClass): 
        The output bounding feature class.
    
    """
    logger.debug("Create cursor to select the outer cross sections")
    field_names = ["SECTIONID"]
    i = 1
    cursor = arcpy.da.SearchCursor(in_cross_sections, field_names)
    for row in cursor:
        if i == 1:
            start = row[0]
        i = i + 1
    end = row[0]
    logger.info(
        "The outer cross sections have the SECTIONID " + str(start)
        + " (start) and " + str(end) + " (end)."
        )
    
    logger.debug("Create feature layer 'layer_temp'.")
    layer_temp = "layer_temp"
    arcpy.MakeFeatureLayer_management(in_cross_sections, layer_temp)
    logger.info("Creating feature layer 'layer_temp' finished successfully.")
    
    logger.debug("Select the outer cross sections.")
    selection_type = "NEW_SELECTION"
    where_clause = "SECTIONID = " + str(start) + " OR SECTIONID = " + str(end)
    arcpy.SelectLayerByAttribute_management(
        layer_temp, selection_type, where_clause)
    logger.info("Outer cross sections selected successfully.")
    
    logger.debug("Create feature class with selected outer cross sections.")
    out_bounding_features = "out_bounding_features"
    arcpy.CopyFeatures_management(layer_temp, out_bounding_features)
    logger.info(
        "Feature class with selected outer cross sections created "
        "successfully."
        )
    
    logger.debug("Delete 'layer_temp'.")
    arcpy.Delete_management(layer_temp)
    logger.info("'layer_temp' deleted successfully.")
    
    return out_bounding_features


def create_cutting_features(in_cross_sections):
    """Create cutting features with cross sections.
    
    With a cursor the cutting cross sections are selected. If the number
    of cross sections is > 2, an inner cross section is selected and 
    saved in an output feature class. If the number of cross sections is
    2, the start cross section and the end cross section is selected and 
    saved to an output feature class. The output is appended to a list.
    
    @param in_cross_sections(DEFeatureClass): 
        The feature class with the input cross sections.
    
    @return out_cutting_features(List): 
        The output cutting feature classes
    
    """
    logger.debug("Create cursor to select the outer cross sections")
    field_names = ["SECTIONID"]
    i = 1
    cursor = arcpy.da.SearchCursor(in_cross_sections, field_names)
    for row in cursor:
        if i == 1:
            start = row[0]
        i = i + 1
    end = row[0]
    i = i - 1
    logger.info(
        "The outer cross sections have the SECTIONID " + str(start) 
        + " (start) and " + str(end) + " (end)."
        )
    
    logger.debug("Create feature layer 'layer_temp'.")
    layer_temp = "layer_temp"
    arcpy.MakeFeatureLayer_management(in_cross_sections, layer_temp)
    logger.info("Creating feature layer 'layer_temp' finished successfully.")
    
    out_cutting_features = []
    if i > 2:
        logger.debug("Select an inner cross section.")
        selection_type = "NEW_SELECTION"
        where_clause = "SECTIONID = " + str(start + 1)
        arcpy.SelectLayerByAttribute_management(
            layer_temp, selection_type, where_clause
            )
        logger.info("An inner section selected successfully.")
    
        logger.debug("Create feature class with selected inner cross section.")
        out_cutting_features_0 = "out_cutting_features_0"
        arcpy.CopyFeatures_management(layer_temp, out_cutting_features_0)
        logger.info(
            "Feature class with selected inner cross section created "
            "successfully."
            )
        
        out_cutting_features.append(out_cutting_features_0)
        
    elif i == 2:
        logger.debug("Select the outer cross section start.")
        selection_type = "NEW_SELECTION"
        where_clause = "SECTIONID = " + str(start)
        arcpy.SelectLayerByAttribute_management(
            layer_temp, selection_type, where_clause)
        logger.info("Outer cross section start selected successfully.")
    
        logger.debug("Create feature class with selected outer cross section.")
        out_cutting_features_0 = "out_cutting_features_0"
        arcpy.CopyFeatures_management(layer_temp, out_cutting_features_0)
        logger.info(
            "Feature class with selected outer cross section created "
            "successfully."
            )
        
        out_cutting_features.append(out_cutting_features_0)
    
        logger.debug("Select the outer cross section end.")
        where_clause = "SECTIONID = " + str(end)
        arcpy.SelectLayerByAttribute_management(
            layer_temp, selection_type, where_clause)
        logger.info("Outer cross section end selected successfully.")
    
        logger.debug("Create feature class with selected outer cross section.")
        out_cutting_features_1 = "out_cutting_features_1"
        arcpy.CopyFeatures_management(layer_temp, out_cutting_features_1)
        logger.info(
            "Feature class with selected outer cross section created "
            "successfully."
            )
        
        out_cutting_features.append(out_cutting_features_1) 
        
    else: 
        try:
            logger.error("Number of cross sections < 2. Execution failed.")
            raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            sys.exit(0)
        
    logger.debug("Delete 'layer_temp'.")
    arcpy.Delete_management(layer_temp)
    logger.info("'layer_temp' deleted successfully.")
    
    return out_cutting_features