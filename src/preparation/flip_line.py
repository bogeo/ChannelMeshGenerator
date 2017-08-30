"""
Created on 14.07.2017

@author: Matthias Hensen

Check and flip line directions or flip line numerations.

function: flip_line_direction(
    workspace, adjusting_features, reference_features, 
    out_features_name, keep_names)
    
function: flip_line_numeration(
    workspace, adjusting_features, out_features_name, keep_names)
                
"""

import logging
import time

import arcpy

from configuration.configure_logging import create_logger

from other.sort_features import sort_features


logger = logging.getLogger(__name__)
create_logger(logger)


def flip_line_direction(
        workspace, adjusting_features, reference_features, out_features_name,
        keep_names, reference_where_clause):
    """Check direction of input lines and flip lines if necessary.
    
    The tool arcpy.FlipLine_edit modifies the input data. If the input
    data should remain unchanged (if keep_names is 'False') the input data
    must be copied. The first points of each input line are copied into
    a feature class. It is checked, if this points touch the reference
    features. If they do not touch the reference features, the lines 
    which belong to the points are flipped.
    
    @param workspace(DEWorkspace):
        The workspace for results.
    @param adjusting_features(DEFeatureClass):
        The feature class with the adjusting input lines.
    @param reference_features(DEFeatureClass):
        The feature class with the reference features.
    @param out_features_name(GPString): 
        The output feature class name.
    @param keep_names(GPBoolean): 
        Input name = output name?
    @param reference_where_clause(GPString):
        The where clause to select reference features
    
    @return out_features(DEFeatureClass): 
        The corrected input lines
    
    """
    if not keep_names:
        logger.debug("Create output feature class.")
        try:
            logger.debug("Create feature class 'temp_features'.")
            temp_features = "temp_features"
            out_features = workspace + "/" + out_features_name
            arcpy.CopyFeatures_management(adjusting_features, temp_features)
            logger.debug("'temp_features' successfully created.")
            arcpy.CopyFeatures_management(temp_features, out_features)
            logger.info(
                "Output feature class " + out_features + " created " 
                "successfully."
                )
            logger.debug("Delete feature class 'temp_features'.")
            arcpy.Delete_management(temp_features)
            logger.debug("'temp_features' deleted successfully.")
        except arcpy.ExecuteError:
            logger.warning(
                out_features + " already exists. Change output name " 
                + out_features + time.strftime("%d%m%y_%H%M%S.")
                )
            out_features = out_features + time.strftime("%d%m%y_%H%M%S")
            arcpy.CopyFeatures_management(adjusting_features, out_features)
            logger.info(
                "Output feature class " + out_features + " created " 
                "successfully."
                )
        adjusting_features = out_features
        
    logger.debug("Get the input lines first points and append them to a list.")
    field_names = ["SHAPE@"]
    cursor = arcpy.da.SearchCursor(adjusting_features, field_names)
    point_list = []
    for row in cursor:
        first_point = row[0].firstPoint
        point_list.append(first_point)
    logger.info("First points appended to list successfully.")

    logger.debug("Create feature class 'first_points'.")
    out_path = workspace + "/"
    out_name = "first_points"
    geometry_type = "POINT"
    template = ""
    has_m = ""
    has_z = "ENABLED"
    desc = arcpy.Describe(adjusting_features)
    spatial_reference = desc.spatialReference    
    arcpy.CreateFeatureclass_management(
        out_path, out_name , geometry_type, template, has_m, has_z,
        spatial_reference
        )
    logger.info("Feature class 'first_points' created successfully.")

    logger.debug("Insert points from list into feature class 'first_points'.")
    first_points = workspace + "/" + out_name
    field_names = ["SHAPE@"]
    with arcpy.da.InsertCursor(first_points, field_names) as cursor:
        for i in range(len(point_list)):
            cursor.insertRow([point_list[i]])
    logger.info(
        "Points from list inserted successfully into feature class "
        "'first_points'."
        )

    logger.debug(
        "Create feature layer 'first_points_layer', "
        "'adjusting_features_layer' and 'reference_features_layer'."
        )
    first_points_layer = "first_points_layer"
    arcpy.MakeFeatureLayer_management(first_points, first_points_layer) 

    adjusting_features_layer = "adjusting_features_layer"
    arcpy.MakeFeatureLayer_management(
        adjusting_features, adjusting_features_layer
        ) 

    reference_features_layer = "reference_features_layer"
    arcpy.MakeFeatureLayer_management(
        reference_features, reference_features_layer, reference_where_clause
        )
    logger.info(
        "Creating feature layer 'first_points_layer', "
        "'adjusting_features_layer' and 'reference_features_layer' finished "
        "successfully."
        )

    logger.debug("Select the features which have the wrong direction.")
    overlap_type = "INTERSECT"
    search_distance = ""
    selection_type = "NEW_SELECTION"
    arcpy.SelectLayerByLocation_management(
        first_points_layer, overlap_type, reference_features_layer, 
        search_distance, selection_type
        )

    overlap_type = "BOUNDARY_TOUCHES"  
    arcpy.SelectLayerByLocation_management(
        adjusting_features_layer, overlap_type, first_points_layer, 
        search_distance, selection_type
        )
    logger.info(
        "Selecting features which have the wrong direction finished "
        "successfully."
        )  

    logger.debug("Flip the direction of this features.")
    arcpy.FlipLine_edit(adjusting_features_layer)
    logger.info(
        "Flipping the direction of this features finished successfully."
        )
    
    logger.debug(
        "Delete feature class 'first_points', feature layer "
        "'first_points_layer', 'adjusting_features_layer' and "
        "'reference_features_layer'."
        )
    arcpy.Delete_management(first_points) 
    arcpy.Delete_management(first_points_layer)
    arcpy.Delete_management(adjusting_features_layer)
    arcpy.Delete_management(reference_features_layer)  
    logger.info(
        "Deleting feature class 'first_points', feature layer "
        "'first_points_layer', 'adjusting_features_layer' and "
        "'reference_features_layer' finished successfully."
        )
    
    return adjusting_features


def flip_line_numeration(
        workspace, adjusting_features, out_features_name, keep_names):
    """Flip the numeration (SECTIONID) of the input feature class.
    
    The tool modifies the input data with a cursor. If the input data
    should remain unchanged (if keep_names is 'False') the input data must
    be copied. The input lines are sorted ascending. The numeration
    (SECTIONID) is flipped with an update cursor.
    
    @param workspace(DEWorkspace):
        The workspace for results.
    @param adjusting_features(DEFeatureClass):
        The feature class with the adjusting input lines. 
    @param out_features_name(GPString):
        The output feature class name.
    @param keep_names(GPBoolean): 
        Input name = output name?
    
    @return adjusting_features(DEFeatureClass): 
        The corrected input lines.
    
    """
    if not keep_names:
        logger.debug("Create output feature class.")
        try:
            logger.debug("Create feature class 'temp_features'.")
            temp_features = "temp_features"
            out_features = workspace + "/" + out_features_name
            arcpy.CopyFeatures_management(adjusting_features, temp_features)
            logger.debug("'temp_features' successfully created.")
            arcpy.CopyFeatures_management(temp_features, out_features)
            logger.info(
                "Output feature class " + out_features + " created "
                "successfully."
                )
            logger.debug("Delete feature class 'temp_features'.")
            arcpy.Delete_management(temp_features)
            logger.debug("'temp_features' deleted successfully.")
        except arcpy.ExecuteError:
            logger.warning(
                out_features + " already exists. Change output name: " 
                + out_features + time.strftime("%d%m%y_%H%M%S.")
                )
            out_features = out_features + time.strftime("%d%m%y_%H%M%S")
            arcpy.CopyFeatures_management(adjusting_features, out_features)
            logger.info(
                "Output feature class " + out_features + " created " 
                "successfully."
                )
            logger.debug("Delete feature class 'temp_features'.")
            arcpy.Delete_management(temp_features)
            logger.debug("'temp_features' deleted successfully.")
        adjusting_features = out_features
    
    logger.debug("Sort adjusting features.")
    sort_field = [["SECTIONID", "ASCENDING"]]
    sort_features(adjusting_features, sort_field)
    logger.info("Sorting adjusting features finished successfully.")
      
    logger.debug("Count adjusting features.")
    result = arcpy.GetCount_management(adjusting_features)
    count = int(result.getOutput(0))
    logger.info("Counting adjusting features finished successfully.")

    logger.debug("Create cursor for flipping the SECTIONIDs.")
    field_names = ["SECTIONID"]
    with arcpy.da.UpdateCursor(adjusting_features, field_names) as cursor:
        for row in cursor:
            row[0] = count
            cursor.updateRow(row)
            count = count - 1
    logger.info("Flipping the SECTIONIDs finished successfully.")
    
    return adjusting_features