"""
Created on 18.07.2017

@author: Matthias Hensen

Interpolate the longitudinal section height (z) values.

function: interpolate_longitudinal_sections(
    workspace, in_longitudinal_section_points,
    in_longitudinal_section_lines, in_cross_section_points, 
    in_cross_section_lines, height_assignment_method, 
    interpolation_method, out_longitudinal_sections_name,
    keep_names)
    
function: assign_height_values(
    in_longitudinal_section_points, in_cross_section_points, 
    in_cross_section_lines, height_assignment_method)
    
function: interpolate_height_values(
    in_longitudinal_section_points, in_longitudinal_section_lines, 
    in_cross_section_lines, interpolation_method)
    
"""

import logging
import math
import time

import arcpy

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def interpolate_longitudinal_sections(
        workspace, in_longitudinal_section_points, 
        in_longitudinal_section_lines, in_cross_section_points, 
        in_cross_section_lines, height_assignment_method,
        interpolation_method, out_longitudinal_sections_name,
        keep_names):
    """Interpolate the longitudinal section height (z) values.
    
    First, the output feature class is created if necessary. Then the 
    function assign_height_values is called and executed to assign the
    original cross section heights to the longitudinal sections with 
    an INTERMEDIATEID = '0'. After that the height values become 
    interpolated with the function interpolate_height_values. Finally
    the coordinates are displayed in the output feature class.
    
    @param workspace(DEWorkspace): 
        The workspace for results.
    @param in_longitudinal_section_points(DEFeatureClass): 
        The longitudinal section points feature class.    
    @param in_longitudinal_section_lines(DEFeatureClass): 
        The longitudinal section lines feature class.
    @param in_corss_section_points(DEFeatureClass): 
        The cross section points feature class.    
    @param in_cross_section_lines(DEFeatureClass): 
        The cross section lines feature class.    
    @param height_assignment_method(GPString): 
        The height assignment method.
    @param interpolation_method(GPString): 
        The interpolation method.     
    @param out_longitudinal_sections_name(GPString): 
        The name of the feature class with the interpolated longitudinal
        sections.
    @param keep_names(GPBoolean):
        Input name = output name?
        
    @return longitudinal_section_points(DEFeatureClass):
        The interpolated longitudinal section points.    
         
    """
    if not keep_names:
        logger.debug("Create output feature class.")
        try:
            out_features = (
                workspace + "/" + out_longitudinal_sections_name
                )
            arcpy.CopyFeatures_management(
                in_longitudinal_section_points, out_features
                )
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
            arcpy.CopyFeatures_management(
                in_longitudinal_section_points, out_features
                )
            logger.info(
                "Output feature class " + out_features + " created " 
                "successfully."
                )
        in_longitudinal_section_points = out_features
        
    logger.debug("Start function assign_height_values.")
    in_longitudinal_section_points = assign_height_values(
        in_longitudinal_section_points, in_cross_section_points, 
        in_cross_section_lines, height_assignment_method
        )    
    logger.info("Assign_height_values finished successfully.")
    
    logger.debug("Start function interpolate_height_values.")
    longitudinal_section_points = interpolate_height_values(
        in_longitudinal_section_points, in_longitudinal_section_lines, 
        in_cross_section_lines, interpolation_method
        )
    logger.info("Interpolate_height_values finished successfully.")
    
    logger.debug("Display Coordinates in the output feature class.")
    arcpy.AddXY_management(longitudinal_section_points)
    logger.debug(
        "Displaying Coordinates in the output feature class finished "
        "successfully."
        )
    
    return longitudinal_section_points


def assign_height_values(
        in_longitudinal_section_points, in_cross_section_points, 
        in_cross_section_lines, height_assignment_method):
    """Assign height (z) values from cross section points to 
    longitudinal section points.
    
    With a cursor the longitudinal section points are selected which
    are located at the cross sections . If the height assignment method
    is 'NEAR_INSIDE_WLB', the height values from the cross section
    points which are located inside the water land border are assigned
    to the selected longitudinal section points with a near analysis. If
    the height assignment method is 'NEAR_ALL', the height values from
    the cross section points are assigned to the selected longitudinal 
    section points with a near analysis, regardless of whether they are
    located inside or outside the water land border. In both cases, the
    height values are assigned to the field 'SHAPE@Z' of the output 
    feature class.
    
    @param in_longitudinal_section_points(DEFeatureClass): 
        The longitudinal section points feature class.    
    @param in_cross_section_points(DEFeatureClass): 
        The cross section points feature class.    
    @param in_cross_section_lines(DEFeatureClass): 
        The cross section lines feature class.    
    @param height_assignment_method(GPString): 
        The height assignment method.
        
    @return in_longitudinal_section_points(DEFeatureClass):
        The longitudinal section points with the assigned height
        values.    
         
    """
    logger.debug("Create feature layer 'longitudinal_section_points_layer'.")
    longitudinal_section_points_layer = "longitudinal_section_points_layer"
    arcpy.MakeFeatureLayer_management(
        in_longitudinal_section_points, longitudinal_section_points_layer
        )
    logger.info(
        "Feature layer 'longitudinal_section_points_layer' created "
        "successfully."
        )
    
    logger.debug("Select Points with an INTERMEDIATEID value = 0.")
    selection_type = "NEW_SELECTION"
    where_clause = "INTERMEDIATEID = 0"
    arcpy.SelectLayerByAttribute_management(
        longitudinal_section_points_layer, selection_type, where_clause
        )
    logger.debug("Points with an INTERMEDIATEID = 0 selected successfully.")

    if height_assignment_method == "NEAR_INSIDE_WLB":
        logger.debug("Create feature layer 'cross_section_points_layer'.")
        cross_section_points_layer = "cross_section_points_layer"
        arcpy.MakeFeatureLayer_management(
            in_cross_section_points, cross_section_points_layer
            )
        logger.info(
            "Feature layer 'cross_section_lines_layer' created successfully."
            )
        
        logger.debug(
            "Select cross section points which are inside the water land "
            "border."
            )
        overlap_type = "INTERSECT"
        search_distance = ""
        selection_type = "NEW_SELECTION"
        arcpy.SelectLayerByLocation_management(
            cross_section_points_layer, overlap_type, in_cross_section_lines,
            search_distance, selection_type
            )
        logger.info(
            "Cross section points which are inside the water land border "
            "selected successfully."
            )
        
        logger.debug("Execute proximity analysis.")
        arcpy.Near_analysis(
            longitudinal_section_points_layer, cross_section_points_layer
            )
        logger.info("Proximity analysis finished successfully.")
        
        logger.debug("Delete feature layer 'cross_section_points_layer'.")
        arcpy.Delete_management(cross_section_points_layer) 
        logger.info(
            "Deleting feature layer 'cross_section_points_layer' finished "
            "successfully."
            ) 
        
    elif height_assignment_method == "NEAR_ALL":
        logger.debug("Execute proximity analysis.")
        arcpy.Near_analysis(
            longitudinal_section_points_layer, in_cross_section_points
            )
        logger.info("Proximity analysis finished successfully.")

    logger.debug("Assign height values.")
    fields_ucursor = ["Near_FID","SHAPE@Z"]
    fields_scursor = ["OBJECTID","SHAPE@Z"]
    with arcpy.da.UpdateCursor(
            longitudinal_section_points_layer, fields_ucursor) as ucursor:
        for urow in ucursor:
            scursor = arcpy.da.SearchCursor(
                in_cross_section_points, fields_scursor
                )
            for srow in scursor:
                if srow[0] == urow[0]:
                    urow[1] = srow[1]
                    break    
            ucursor.updateRow(urow)
    logger.info("Height values assigned successfully.")  
    
    logger.debug("Delete feature layer 'longitudinal_section_points_layer'.")
    arcpy.Delete_management(longitudinal_section_points_layer) 
    logger.info(
        "Deleting feature layer 'longitudinal_section_points_layer' finished "
        "successfully."
        )
    
    return in_longitudinal_section_points 


def interpolate_height_values(
        in_longitudinal_section_points, in_longitudinal_section_lines, 
        in_cross_section_lines, interpolation_method):
    """Interpolate height (z) values.
    
    First the count of the cross sections and the longitudinal sections
    is determined. If the interpolation method is 'LINEAR', the
    longitudinal section points height (z) values between each successive 
    cross sections are interpolated. The interpolation is performed with
    the formula:
    
        z_current = z_previous + (z_end - z_start) * distance / length
        
    The variables mean:
    
        z_current:  the current points height
        z_pervious: the previous points height
        z_end:      the end points height
        z_start:    the start points height
        distance:   the distance between the current point and the 
                    previous point
        length:     the longitudinal section parts length (the length of
                    the interpolated part)
                    
    After the interpolation the height values are assigned to the field
    'SHAPE@Z' of the output feature class.
    
    @param in_longitudinal_section_points(DEFeatureClass): 
        The longitudinal section points feature class. 
    @param in_longitudinal_section_lines(DEFeatureClass): 
        The longitudinal section lines feature class.          
    @param in_cross_section_lines(DEFeatureClass): 
        The cross section lines feature class.     
    @param interpolation_method(GPString): 
        The interpolation method.
        
    @return in_longitudinal_section_points(DEFeatureClass):
        The interpolated longitudinal section points.    
         
    """
    logger.debug("Count cross sections.")
    result = arcpy.GetCount_management(in_cross_section_lines)
    count_cross_sections = int(result.getOutput(0))
    logger.info("Counting cross sections finished successfully.")
    
    logger.debug("Count longitudinal sections.")
    result = arcpy.GetCount_management(in_longitudinal_section_lines)
    count_longitudinal_sections = int(result.getOutput(0))
    logger.info("Counting longitudinal sections finished successfully.")
    
    logger.debug("Create feature layer 'longitudinal_section_points_layer'.")
    longitudinal_section_points_layer = "longitudinal_section_points_layer"
    arcpy.MakeFeatureLayer_management(
        in_longitudinal_section_points, longitudinal_section_points_layer
        )
    logger.info(
        "Feature layer 'longitudinal_section_points_layer' created "
        "successfully."
        )

    if interpolation_method == "LINEAR":
        logger.debug("Start interpolating height (z) values.")
        x_coordinates = []
        y_coordinates = []
        distances_between_successive_points = []
        height_values = []
        for i in range (1, count_cross_sections):
            for j in range (1, count_longitudinal_sections + 1):
                logger.debug(
                    "Select longitudinal section points for longitudinal "
                    "section part " + str(j) + " between cross section " 
                    + str(i) + " and cross section " + str(i + 1)
                    )
                selection_type = "NEW_SELECTION"
                where_clause = (
                    "(SECTIONID = " + str(i) + " AND POINTID = " + str(j) 
                    + ") OR (SECTIONID = " + str(i + 1) + " AND POINTID = " 
                    + str(j) + " AND INTERMEDIATEID = 0)"
                    )
                arcpy.SelectLayerByAttribute_management(
                    longitudinal_section_points_layer, selection_type,
                    where_clause
                    )
            
                logger.debug("Create search cursor. ")
                field_names = [
                    "SHAPE@X", "SHAPE@Y", "SHAPE@Z", "SECTIONID",
                    "INTERMEDIATEID"
                    ]
                cursor = arcpy.da.SearchCursor(
                    longitudinal_section_points_layer, field_names
                    )
                logger.debug(
                    "Add x and y coordinates to the lists and determine the "
                    "start and end cross section height (z) values."
                    )
                for row in cursor:
                    x_coordinates.append(row[0])
                    y_coordinates.append(row[1])
                    if row[3] == i and row[4] == 0:
                        z_start = row[2]
                    elif row[3] == i + 1 and row[4] == 0:
                        z_end = row[2]
            
                logger.debug("Compute the longitudinal section parts length. ")
                count_x_coordinates = len(x_coordinates)
                length_longitudinal_section_part = 0
                for k in range(count_x_coordinates - 1):
                    distance_between_successive_points = math.sqrt(
                        math.pow(x_coordinates[k + 1] - x_coordinates[k], 2) 
                        + math.pow(y_coordinates[k + 1] - y_coordinates[k], 2)
                        )
                    length_longitudinal_section_part = (
                        length_longitudinal_section_part 
                        + distance_between_successive_points
                        )
                    distances_between_successive_points.append(
                        distance_between_successive_points
                        )
            
                logger.debug("Interpolate the height (z) values.")
                count_distances_between_successive_points = len(
                    distances_between_successive_points
                    )
                z_previous_point = z_start
                for m in range(count_distances_between_successive_points - 1):
                    z_current_point = (
                        z_previous_point + (z_end - z_start)
                        *distances_between_successive_points[m] 
                        /length_longitudinal_section_part
                        )
                    z_previous_point = z_current_point
                    z_current_point = round(z_current_point, 2)
                    height_values.append(z_current_point)
            
                logger.debug("Assign height (z) values to field SHAPE@Z")
                field_names = ["SHAPE@Z"]
                where_clause = "INTERMEDIATEID > 0"
                with arcpy.da.UpdateCursor(
                        longitudinal_section_points_layer, field_names,
                        where_clause) as cursor:
                    n = 0
                    for row in cursor:
                        row[0] = height_values[n]
                        cursor.updateRow(row)
                        n = n + 1
                logger.debug("Empty lists.")
                del x_coordinates[:]
                del y_coordinates[:]
                del distances_between_successive_points[:]
                del height_values[:]
    
        logger.info("Interpolating height (z) values finished successfullly.")
    
    logger.debug("Delete feature layer 'longitudinal_section_points_layer'.")
    arcpy.Delete_management(longitudinal_section_points_layer)
    logger.info(
        "Feature layer 'longitudinal_section_points_layer' deleted "
        "successfully."
        )
    
    return in_longitudinal_section_points