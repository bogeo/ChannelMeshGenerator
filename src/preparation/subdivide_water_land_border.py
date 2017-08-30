"""
Created on 15.07.2017

@author: Matthias Hensen

Subdivide the water land border at the cross sections.

function: subdivide_water_land_border(
    workspace, in_wlb, in_cross_sections, out_wlb_subdivided_name,
    keep_names)
    
"""

import logging
import time

import arcpy

from configuration.configure_logging import create_logger

from other.list_field_names import list_field_names


logger = logging.getLogger(__name__)
create_logger(logger)


def subdivide_water_land_border(
        workspace, in_wlb, in_cross_sections, out_wlb_subdivided_name,
        keep_names):
    """Subdivide the water land border at the cross sections.
    
    First it is checked, if a field SECTIONID exists in the input water
    land border feature class. This is necessary for preventing that two
    fields with the name SECTIONID would exist after executing the 
    function FeatureToLine. For the numbering of the water land border 
    parts, a clear field SECTIONID is necessary. If a field exists, it 
    is deleted. Then a field WLBID is added. The tool FeatureToLine is
    executed to split water land border and cross sections at their
    intersections. Each water land border part gets the SECTIONID from
    the cross section between which it is located. For that, the lower
    SECTIONID is allocated. After that, the cross sections become
    deleted and the output feature class is created. At the end, it is
    checked if the count of water land border parts is meeting the
    expectations or if there was a error during the subdividing process.
    
    @param workspace(DEWorkspace): 
        The workspace for results.
    @param in_wlb(DEFeatureClass):
        The input water land border feature class.    
    @param in_cross_sections(DEFeatureClass):
        The input cross sections feature class.    
    @param out_wlb_subdivided_name(GPString):
        The name of the feature class with the subdivided water land
        border.    
    @param keep_names(GPBoolean):
        Input name = output name?
        
    @return out_features(DEFeatureClass): 
        The feature class with the subdivided water land border.
         
    """
    logger.debug(
        "Check if field SECTIONID exists in the input water land border "
        "feature class. If existing, it is deleted."
        )
    field_names = list_field_names(in_wlb)
    field_name = "SECTIONID"
    if field_name in field_names:
        arcpy.DeleteField_management(in_wlb, field_name)
        logger.info("Field SECTIONID deleted successfully.")
    
    logger.debug("Add a field WLBID to the water land border feature class.")
    field_name = "WLBID"
    field_type = "SHORT"
    arcpy.AddField_management(in_wlb, field_name, field_type)
    logger.info("Field WLBID added successfully.")
    
    logger.debug("Create cursor for allocating the WLBID.")
    field_names = ["WLBID"]
    with arcpy.da.UpdateCursor(in_wlb, field_names) as cursor:
        i = 1
        for row in cursor:
            if (row[0] != 1 and row[0] != 2):
                row[0] = i
                cursor.updateRow(row)
                i = i + 1
    logger.info("WLBID set successfully.")
    
    logger.debug(
        "Split water land border and cross sections at their intersections."
        )
    in_features = [in_wlb, in_cross_sections]
    temp_features = "temp_features"
    arcpy.FeatureToLine_management(in_features, temp_features)
    logger.info("Splitting features finished successfully.")

    logger.debug("Create feature layer 'temp_layer'.")
    temp_layer = "temp_layer"
    arcpy.MakeFeatureLayer_management(temp_features, temp_layer)
    logger.info("'temp_layer' created successfully.")
    
    logger.debug("Count cross sections.")
    result = arcpy.GetCount_management(in_cross_sections)
    count_cross_sections = int(result.getOutput(0))
    logger.info("Counting cross sections finished successfully.")

    logger.debug("Start numbering the water land border parts.")
    for i in range(count_cross_sections):
        selection_type = "NEW_SELECTION"
        where_clause = "SECTIONID = " + str(i + 1)
        arcpy.SelectLayerByAttribute_management(
            temp_layer, selection_type, where_clause
            )

        overlap_type = "BOUNDARY_TOUCHES"
        search_distance = ""
        arcpy.SelectLayerByLocation_management(
            temp_layer, overlap_type, temp_layer, search_distance,
            selection_type
            )
    
        field_names = ["SECTIONID"]
        with arcpy.da.UpdateCursor(temp_layer, field_names) as cursor:
            for row in cursor:
                row[0] = i
                cursor.updateRow(row)
    logger.info("Numbering the water land border parts finished successfully.")
    
    logger.debug(
        "Select and delete elements which are not part of the water land "
        "border."
        )
    where_clause = "WLBID = 0"
    arcpy.SelectLayerByAttribute_management(
        temp_layer, selection_type, where_clause
        )
    arcpy.DeleteFeatures_management(temp_layer)
    logger.info(
        "Elements which are not part of the water land border deleted "
        "successfully."
        )
    
    logger.debug("Create output feature class.")
    if keep_names:
        out_features = in_wlb
        arcpy.CopyFeatures_management(temp_layer, out_features)
        logger.info(
            "Output feature class " + out_features + " created successfully."
            )
    else:
        try:
            out_features = workspace + "/" + out_wlb_subdivided_name
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
        
    logger.debug("Check if subdividing water land border was successful.")
    result = arcpy.GetCount_management(out_features)
    count_divided_wlb = int(result.getOutput(0))
    if count_divided_wlb == 2*count_cross_sections - 2:
        logger.info("Subdividing water land border was successful.")
    else:
        logger.warning(
            "Number of water land border parts and number of cross sections "
            "are incompatible. There are " + str (count_divided_wlb) + " "
            "water land border parts. There must be " 
            + str(count_cross_sections - 2) + " parts."
            ) 
        
    return out_features   