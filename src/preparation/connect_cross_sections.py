"""
Created on 02.06.2017

@author: Matthias Hensen

Connect the points from the cross sections to lines.

function: connect_cross_sections_with_indication(
    workspace, in_cross_sections, out_cross_sections_name, line_field,
    maximum_distance)
    
function: connect_cross_sections_without_indication(
    workspace, in_cross_sections, out_cross_sections_name, maximum_distance)
    
function: check_duplicated_cross_sections(in_cross_sections)
                
"""

import logging
import math
import time

import arcpy

from configuration.configure_logging import create_logger

from other.list_field_names import list_field_names


logger = logging.getLogger(__name__)
create_logger(logger)


def connect_cross_sections_with_indication(
            workspace, in_cross_sections, out_cross_sections_name, line_field,
            maximum_distance):
    """Connect the points from the cross sections to lines.
        
    An indication (e.g. a kilometer indication) is used as line field
    for the connection. If the named line_field is not avaiable, the
    function connect_cross_sections_without_indication is called. 
    Else, after connecting the cross sections, a field 'SECTIONID'
    and a field 'INTERMEDIATEID' are added to the output feature class.
    The SECTIONID begins with 1 and is incremented. The INTERMEDIATEID
    is set to 0.
    
    @param workspace (DEWorkspace):
        The workspace for results.
    @param in_cross_sections (DEFeatureClass): 
        The feature class with the cross sections points.
    @param out_cross_sections out_cross_sections (GPString): 
        The output feature class name.
    @param line_field (GPString): 
        The line fields name.
    @param maximum_distance (GPDouble):
        The maximum distance between points.
    
    @return out_cross_sections(DEFeatureClass): 
        The output cross section feature class.
    
    """ 
    logger.debug("Check if line_field '" + line_field +"' exists.")
    field_names = list_field_names(in_cross_sections)
        
    if line_field in field_names:    
        logger.debug("Start connecting cross sections to lines.")
        try:
            out_cross_sections = workspace + "/" + out_cross_sections_name
            arcpy.PointsToLine_management(
                in_cross_sections, out_cross_sections, line_field
                )
        except arcpy.ExecuteError:
            logger.warning(
                out_cross_sections + " already exists. Change output name: " 
                + out_cross_sections + time.strftime("%d%m%y_%H%M%S.")
                )
            out_cross_sections = (
                out_cross_sections + time.strftime("%d%m%y_%H%M%S")
                )
            arcpy.PointsToLine_management(
                in_cross_sections, out_cross_sections, line_field
                )
        logger.info("Connecting cross sections completed successfully.")

        logger.debug("Add a field SECTIONID.")
        field_name = "SECTIONID"
        field_type = "SHORT"
        arcpy.AddField_management(out_cross_sections, field_name, field_type)
        logger.info("Field SECTIONID added successfully.")
    
        logger.debug("Add a field INTERMEDIATEID.")
        field_name = "INTERMEDIATEID"
        arcpy.AddField_management(out_cross_sections, field_name, field_type)
        logger.info("Field INTERMEDIATEID added successfully.")
    
        logger.debug("Create cursor for allocating the IDs.")
        field_names = ["SECTIONID", "INTERMEDIATEID"]
        with arcpy.da.UpdateCursor(out_cross_sections, field_names) as cursor:
            i = 1
            for row in cursor:
                row[0] = i
                row[1] = 0
                cursor.updateRow(row)
                i = i + 1
        logger.info(
            "Set SECTIONID successfully: " + str (i) + " cross sections "
            "exist. Set INTERMEDIATEID successfully to 0."
            )

        return out_cross_sections
    
    else:
        logger.warning(
            "Line_field '" + line_field + "' does not exist. Start function "
            "connect_cross_sections_without_indication."
            )
        out_cross_sections = connect_cross_sections_without_indication(
            workspace, in_cross_sections, out_cross_sections_name,
            maximum_distance
            )
        
        return out_cross_sections
    

def connect_cross_sections_without_indication(
            workspace, in_cross_sections, out_cross_sections_name,
            maximum_distance):
    """Connect the points from the cross sections to lines.
        
    The function arcpy.PointsToLine_management(in_features,
    out_features, line_field) needs a line_field to connect points which
    belong together. For this, a line_field is created in this function.
    Therefore a field 'SECTIONID' is added to the in_cross_section
    feature class. Then, the coordinates of the points are transfered
    into point_list with a cursor. After that, the distance between
    successive points is computed. If the distance is less than the 
    maximum_distance, the cursor sets the SECTIONID for the point to the
    current value (starts with 1). If the maximum_distance is greater than
    the distance, the next distance is not computed. The point after
    next and the following points with a distance less maximum_distance get
    a SECTIONID + 1. After computing all distances between successive 
    points in this way, the SECTIONID is used as line field for the
    connection. After connecting the cross sections, a field 
    'INTERMEDIATEID' is added to the output feature class and set to 0
    with a cursor. 
    
    @param workspace (DEWorkspace): 
        The workspace for results.
    @param in_cross_sections (DEFeatureClass): 
        The feature class with the cross sections points.
    @param out_cross_sections (GPString): 
        The output feature class name.
    @param maximum_distance (GPDouble): 
        The maximum distance between points.
    
    @return out_cross_sections(DEFeatureClass): 
        The output cross section feature class.
    
    """ 
    logger.debug("Add a field SECTIONID.")
    field_name = "SECTIONID"
    field_type = "SHORT"
    arcpy.AddField_management(in_cross_sections, field_name, field_type)
    logger.info("Field SECTIONID added successfully.")

    logger.debug("Transfer coordinates into list point_list.")
    point_list = []
    field_names = ["SHAPE@X", "SHAPE@Y", "SHAPE@Z", "SECTIONID"]
    with arcpy.da.UpdateCursor(in_cross_sections, field_names) as cursor:
        for row in cursor:    
            point_list.append([row[0], row[1], row[2]])
    logger.info(str(len(point_list)) + " points transferred into point_list.")
        
    cursor.reset()

    logger.debug("Start creating the line_field SECTIONID.")
    i = 0
    j = 1
    for row in cursor:
        if i < (len(point_list) - 1):
            distance = (
                math.sqrt(math.pow(point_list[i + 1][0] - point_list[i][0], 2) 
                + math.pow(point_list[i + 1][1] - point_list[i][1], 2)
                + math.pow(point_list[i + 1][2] - point_list[i][2], 2))
                )
        row[3] = j
        cursor.updateRow(row)
        if distance > maximum_distance:
            j = j + 1
        i = i + 1
    logger.info("Set SECTIONID successfully until " + str (j) + ".")

    logger.debug("Start connecting cross sections to lines.")
    try:
        out_cross_sections = workspace + "/" + out_cross_sections_name
        line_field = "SECTIONID"
        arcpy.PointsToLine_management(
            in_cross_sections, out_cross_sections, line_field
            )
    except arcpy.ExecuteError:
        logger.warning(
            out_cross_sections + " already exists. Change output name: " 
            + out_cross_sections + time.strftime("%d%m%y_%H%M%S.")
            )
        out_cross_sections = (
            out_cross_sections + time.strftime("%d%m%y_%H%M%S")
            )
        arcpy.PointsToLine_management(
            in_cross_sections, out_cross_sections, line_field
            )
    logger.info("Connecting cross sections completed successfully.")
    
    logger.debug("Add a field INTERMEDIATEID.")
    field_name = "INTERMEDIATEID"
    arcpy.AddField_management(out_cross_sections, field_name, field_type)
    logger.info("Field INTERMEDIATEID added successfully.") 

    logger.debug("Create cursor for allocating the IDs.")
    field_names = ["INTERMEDIATEID"] 
    with arcpy.da.UpdateCursor(out_cross_sections, field_names) as cursor:
        for row in cursor:
            row[0] = 0
            cursor.updateRow(row)
    logger.info("Set INTERMEDIATEID successfully to 0.")
    
    return out_cross_sections


def check_duplicated_cross_sections(in_cross_sections):
    """Check if duplicated cross sections exist and delete one of them.
    
    First, the total number of cross sections is counted. A feature
    layer is created to select successive cross sections. For the
    selected cross sections it is checked, if their center is in the 
    other cross section. In this case the number of selected layers is
    2, otherwise the number is 1. If the number is 2, one of the two 
    cross sections (the first) is deleted. Finally, it is checked if 
    this case occured at all. If this is true, the SECTIONID is 
    adjusted to the correct values.
    
    @param in_cross_sections (DEFeatureClass): 
        The feature class with the cross sections.
        
    @return in_cross_sections (DEFeatureClass): 
        The feature class with the checked cross sections.
    
    """
    logger.debug("Get the total number of cross sections.")
    result = arcpy.GetCount_management(in_cross_sections)
    count = int(result.getOutput(0))

    logger.debug("Create feature layer 'cross_sections_layer' ." )
    cross_sections_layer = "cross_sections_Layer"
    arcpy.MakeFeatureLayer_management(in_cross_sections, cross_sections_layer)
    logger.info("'cross_sections_layer' successfully created.")

    delete_in_cross_sections = False
    logger.debug(
        "Select successive cross sections and check if they have their center "
        "in the other cross section."
        )
    for i in range(1, count):
        selection_type = "NEW_SELECTION"
        where_clause = ("SECTIONID = " + str(i) or "SECTIONID = " + str(i + 1))
        arcpy.SelectLayerByAttribute_management(
            cross_sections_layer, selection_type, where_clause
            )
    
        overlap_type = "HAVE_THEIR_CENTER_IN"
        search_distance = ""
        arcpy.SelectLayerByLocation_management(
            cross_sections_layer, overlap_type, cross_sections_layer,
            search_distance, selection_type
            )
    
        result = arcpy.GetCount_management(cross_sections_layer)
        count_in_cross_sections = int(result.getOutput(0))
    
        if count_in_cross_sections == 2:
            logger.debug(
                "'count_in_cross_sections' = 2. Delete first cross section "
                "with number " + str(i) + "."
                )
            field_names = ["SHAPE@"] 
            with arcpy.da.UpdateCursor(
                    cross_sections_layer, field_names) as cursor:
                for row in cursor:
                    cursor.deleteRow()
                    delete_in_cross_sections = True
                    break
                
    j = 1

    if delete_in_cross_sections:
        logger.debug("Correct SECTIONID.")
        field_names = ["SECTIONID"] 
        with arcpy.da.UpdateCursor(in_cross_sections, field_names) as cursor:
            for row in cursor:
                row[0] = j
                cursor.updateRow(row)
                j = j + 1
    logger.info("Corrected number of cross sections: " + str(j - 1) + ".")
    
    logger.debug("Delete layer '" + cross_sections_layer + "'.")
    arcpy.Delete_management(cross_sections_layer)
    logger.info("'" + cross_sections_layer + "' successfully deleted.")
    
    return in_cross_sections