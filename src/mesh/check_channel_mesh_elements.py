"""
Created on 25.07.2017

@author: Matthias Hensen

Check the element area and angle sizes.

function: check_channel_mesh_elements(
    in_channel_mesh_elements, check_angles, check_areas, minimum_angle,
    maximum_angle, area_factor, out_directory, out_file_name, 
    overwrite_output)
    
function: point_a_x, point_a_y, point_a_z, point_b_x, point_b_y, 
    point_b_z, point_c_x, point_c_y, point_c_z)
    
"""

import logging
import math
import os
import sys
import time

import arcpy

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def check_channel_mesh_elements(
        in_channel_mesh_elements, check_angles, check_areas, minimum_angle,
        maximum_angle, area_factor, out_directory, out_file_name,
        overwrite_output):
    """Check the element area and angle sizes.
    
    First, a feature layer is created and the channel mesh elements 
    are counted. Then a cursor check_cursor selects each element. If 
    check_angles is 'True', the vertex coordinates are appended to lists
    and afterwards the last coordinate is deleted from the list because 
    the last point is equal to the first point for a polygon. Then the
    angles are computed with the function compute_angle and appended to
    an angle list. For each angle it is checked if the value is lower or
    larger than the minimum or maximum angle value. In this case a
    warning message is created and appended to a list angle_messages. If
    check_areas is 'True', the elements are selected as reference
    elements which intersect (touch) the current element. If a triangle
    is selected (as reference element or as current check element) the
    area is doubled to compare the areas. Then it is checked if the 
    check elements area value is undersized or oversized compared with
    each reference element. In this case a warning message is created 
    and appended to a list area_messages. After checking all elements
    in this way, the warning messages are written to the output file.
        
    @param in_channel_mesh_elements(DEFeatureClass):
        The input channel mesh elements feature class.
    @param check_angles(GPBoolean):
        Check the angle sizes?
    @param check_areas(GPBoolean):
        Check the area sizes?
    @param minimum_angle(GPLong):
        The minimum angle size
    @param maximum_angle(GPLong):
        The maximum angle size.
    @param area_factor(GPLong):
        The area factor. 
    @param out_directory(DEFolder):
        The directory which will contain the output file.
    @param out_file_name(GPString): 
        The name of the output file. 
    @param overwrite_output(GPBoolean):
        Overwrite output?
            
    @return out_file(DEFile): 
        The output file with the warning messages.
         
    """
    logger.debug("Create feature layer 'channel_mesh_elements_layer'.")
    channel_mesh_elements_layer = "channel_mesh_elements_layer"
    arcpy.MakeFeatureLayer_management(
        in_channel_mesh_elements, channel_mesh_elements_layer
        )
    logger.info(
        "Feature layer 'channel_mesh_elements_layer' created successfully."
        )
    
    logger.debug("Count channel mesh elements.")
    result = arcpy.GetCount_management(in_channel_mesh_elements)
    count_channel_mesh_elements = int(result.getOutput(0))
    logger.info("Counting cross lines finished successfully.")

    logger.debug("Start checking each element.")
    x_coordinates = []
    y_coordinates = []
    z_coordinates = []
    angles = []
    triangle_angle_messages = []
    rectangle_angle_messages = []
    area_messages = []
    i = 1
    for i in range(1, count_channel_mesh_elements + 1):
        logger.debug("Check element " + str(i) + ".")
        field_names = [
            "SHAPE@", "OBJECTID", "SECTIONID", "INTERMEDIATEID", "ELEMENTID",
            "Shape_Area", "Vertex_Cnt"
            ]
        where_clause = "OBJECTID = " + str(i)
        check_cursor = arcpy.da.SearchCursor(
            in_channel_mesh_elements, field_names, where_clause
            )
        for check_row in check_cursor:
            if check_angles:
                logger.debug(
                    "Get points and append point coordinates to lists "
                    "x_coordinates, y_coordinates and z_coordinates. Delete "
                    "the last point (the fist point is equal to the last "
                    "point) and count the points."
                    )
                for part in check_row[0]:
                    for point in part:
                        x_coordinates.append(point.X)
                        y_coordinates.append(point.Y)
                        z_coordinates.append(point.Z)
                x_coordinates.pop()
                y_coordinates.pop()
                z_coordinates.pop()
                count_points = len(x_coordinates)
            
                logger.debug("Compute the first angle.")
                point_a_x = x_coordinates[0]
                point_a_y = y_coordinates[0]
                point_a_z = z_coordinates[0]
                point_b_x = x_coordinates[1]
                point_b_y = y_coordinates[1]
                point_b_z = z_coordinates[1]
                point_c_x = x_coordinates[count_points - 1]
                point_c_y = y_coordinates[count_points - 1]
                point_c_z = z_coordinates[count_points - 1]
                first_angle = compute_angle(
                    point_a_x, point_a_y, point_a_z, point_b_x, point_b_y,
                    point_b_z, point_c_x, point_c_y, point_c_z
                    )
                angles.append(first_angle)
            
                logger.debug("Compute the second angle.")
                point_a_x = x_coordinates[1]
                point_a_y = y_coordinates[1]
                point_a_z = z_coordinates[1]
                point_b_x = x_coordinates[2]
                point_b_y = y_coordinates[2]
                point_b_z = z_coordinates[2]
                point_c_x = x_coordinates[0]
                point_c_y = y_coordinates[0]
                point_c_z = z_coordinates[0]
                second_angle = compute_angle(
                    point_a_x, point_a_y, point_a_z, point_b_x, point_b_y,
                    point_b_z, point_c_x, point_c_y, point_c_z
                    )
                angles.append(second_angle)
            
                if count_points == 4:
                    logger.debug("Compute the third angle.")
                    point_a_x = x_coordinates[2]
                    point_a_y = y_coordinates[2]
                    point_a_z = z_coordinates[2]
                    point_b_x = x_coordinates[1]
                    point_b_y = y_coordinates[1]
                    point_b_z = z_coordinates[1]
                    point_c_x = x_coordinates[3]
                    point_c_y = y_coordinates[3]
                    point_c_z = z_coordinates[3]
                    third_angle = compute_angle(
                        point_a_x, point_a_y, point_a_z, point_b_x, point_b_y,
                        point_b_z, point_c_x, point_c_y, point_c_z
                        )
                    angles.append(third_angle)
                
                    logger.debug("Compute the fourth angle.")
                    fourth_angle = 360 - (first_angle+second_angle+third_angle)
                    fourth_angle = round(fourth_angle, 2)
                    angles.append(fourth_angle)
                
                else:
                    logger.debug("Compute the third angle.")
                    third_angle = 180 - (first_angle+second_angle)
                    third_angle = round(third_angle, 2)
                    angles.append(third_angle)
                
                if count_points == 4:
                    element = "Rectangle"
                else:
                    element = "Triangle"
                
                
                for angle in angles:
                    if angle < minimum_angle:
                        message = (
                            element + " with OBJECTID " + str(check_row[1]) 
                            + " (SECTIONID " + str(check_row[2]) 
                            + ", INTERMEDIATEID " + str(check_row[3]) 
                            + ", ELEMENTID " + str(check_row[4]) + ") has an "
                            "angle of " + str(angle) + " degrees which is "
                            "lower than the minimum angle of " 
                            + str(minimum_angle) + " degrees."
                            )
                        if element == "Rectangle":
                            rectangle_angle_messages.append(message)
                        else:
                            triangle_angle_messages.append(message)
                        logger.warning(message)
                    elif angle > maximum_angle:
                        message = (
                            element + " with OBJECTID " + str(check_row[1]) 
                            + " (SECTIONID " + str(check_row[2]) 
                            + ", INTERMEDIATEID " + str(check_row[3]) 
                            + ", ELEMENTID " + str(check_row[4]) + ") has an "
                            "angle of " + str(angle) + " degrees which is "
                            "larger than the minimum angle of " 
                            + str(maximum_angle) + " degrees."
                            )
                        if element == "Rectangle":
                            rectangle_angle_messages.append(message)
                        else:
                            triangle_angle_messages.append(message)
                        logger.warning(message)
            
                logger.debug("Clear lists.")
                del x_coordinates[:]
                del y_coordinates[:]
                del z_coordinates[:]
                del angles[:]
            
            if check_areas:
                logger.debug(
                    "Select reference elements and check if their area is "
                    "within the area factor. If the check element or the "
                    "reference element is a triangle, the area is multiplied "
                    "by 2."
                    )
                overlap_type = "INTERSECT"
                search_distance = ""
                selection_type = "NEW_SELECTION"
                arcpy.SelectLayerByLocation_management(
                    channel_mesh_elements_layer, overlap_type, check_row[0],
                    search_distance, selection_type
                    )
                field_names = [
                    "OBJECTID", "SECTIONID", "INTERMEDIATEID", "ELEMENTID",
                    "Shape_Area", "Vertex_Cnt"
                    ]
                reference_cursor = arcpy.da.SearchCursor(
                    channel_mesh_elements_layer, field_names
                    )
                for reference_row in reference_cursor:
                    check_area = check_row[5]
                    reference_area = reference_row[4]
                    if check_row[6] == 4:
                        check_area = check_area * 2
                    if reference_row[5] == 4:
                        reference_area = reference_area * 2
                    if check_area < reference_area / float(area_factor):
                        message = (
                            "Element with OBJECTID " + str(check_row[1]) 
                            + " (SECTIONID " + str(check_row[2]) 
                            + ", INTERMEDIATEID " + str(check_row[3]) 
                            + ", ELEMENTID " + str(check_row[4]) + ") has an "
                            "area of " + str(check_area) + " square meters. "
                            "The minimum area of the element should be " 
                            + str(reference_area / float(area_factor)) 
                            + " square meters. The element is undersized "
                            "compared with the element with OBJECTID " 
                            + str(reference_row[0]) + " (SECTIONID " 
                            + str(reference_row[1]) + ", INTERMEDIATEID " 
                            + str(reference_row[2]) + ", ELEMENTID " 
                            + str(reference_row[3]) + ") with an area of " 
                            + str(reference_area) + " square meters."                 
                            )
                        area_messages.append(message)
                        logger.warning(message)
                    elif check_area > area_factor * reference_area:
                        message = (
                            "Element with OBJECTID " + str(check_row[1]) 
                            + " (SECTIONID " + str(check_row[2]) 
                            + ", INTERMEDIATEID " + str(check_row[3]) 
                            + ", ELEMENTID " + str(check_row[4]) + ") has an "
                            "area of " + str(check_area) + " square meters. "
                            "The maximum area of the element should be " 
                            + str(area_factor * reference_area) + " square "
                            "meters. The element is oversized compared with "
                            "the element with OBJECTID " 
                            + str(reference_row[0]) + " (SECTIONID " 
                            + str(reference_row[1]) + ", INTERMEDIATEID " 
                            + str(reference_row[2]) + ", ELEMENTID " 
                            + str(reference_row[3]) + ") with an area of " 
                            + str(reference_area) + " square meters." 
                            )    
                        area_messages.append(message)
                        logger.warning(message)
    
    logger.debug("Delete feature layer ' channel_mesh_elements_layer'.")
    arcpy.Delete_management(channel_mesh_elements_layer)
    logger.info(
        "Feature layer 'channel_mesh_elements_layer' deleted successfully."
        )
    
    logger.debug("Write messages to output file.")
    
    folder_name = out_file_name
    arcpy.CreateFolder_management(out_directory, folder_name)
    out_file = out_directory + "/" + folder_name + "/" + out_file_name + ".txt"
    if (not overwrite_output and os.path.isfile(out_file)):
        logger.warning(
            out_file + " already exists. Change output folder and file name: "
            + out_directory + "/" + folder_name 
            + time.strftime("%d%m%y_%H%M%S/") + out_file_name 
            + time.strftime("%d%m%y_%H%M%S.txt")
            )
        folder_name = folder_name + time.strftime("%d%m%y_%H%M%S")
        arcpy.CreateFolder_management(out_directory, folder_name)
        out_file = (
            out_directory + "/" + folder_name + "/" + out_file_name
            + time.strftime("%d%m%y_%H%M%S") + ".txt"
            )        
    try:
        i = 1
        with open(out_file, "w") as f:
            f.write(
                "Checked feature class: " + in_channel_mesh_elements + "\n"
                "Element count: " + str(count_channel_mesh_elements) + "\n"
                )
            if check_angles:
                f.write(
                    "Warnings for angles (minimum angle: " + str(minimum_angle) 
                    + " degrees, maximum angle: " + str(maximum_angle) 
                    + " degrees):\n"
                    )
                for message in rectangle_angle_messages:
                    f.write(str(i) + ": " + message + "\n")
                    i = i + 1
                f.write("\n")
                for message in triangle_angle_messages:
                    f.write(str(i) + ": " + message + "\n")
                    i = i + 1
            if check_areas:
                f.write(
                    "\nWarnings for areas (area_factor: " + str(area_factor) 
                    + "):\n"
                    )
                for message in area_messages:
                    f.write(str(i) + ": " + message + "\n")
                    i = i + 1
        logger.info("Writing messages to output file finished successfully.")
    except IOError:
        logger.error("Writing messages to output file failed.")
        sys.exit(0)
        
    return out_file


def compute_angle(
        point_a_x, point_a_y, point_a_z, point_b_x, point_b_y, point_b_z,
        point_c_x, point_c_y, point_c_z):
    """Compute cutting angle between two straight lines.
    
    The angle is computed with the formula:
    
       angle = arccos(
           (vector_b*vector_c) / ((amount(vector_b))*(amount(vector_c))
           )
        
    @param point_a_x(GPDouble):
        The x coordinate of point a.
    @param point_a_y(GPDouble):
        The y coordinate of point a.
    @param point_a_z(GPDouble):
        The z coordinate of point a.
    @param point_b_x(GPDouble):
        The x coordinate of point b.
    @param point_b_y(GPDouble):
        The y coordinate of point b.
    @param point_b_z(GPDouble):
        The z coordinate of point b.
    @param point_c_x(GPDouble):
        The x coordinate of point c.
    @param point_c_y(GPDouble):
        The y coordinate of point c.
    @param point_c_z(GPDouble):
        The z coordinate of point c.
            
    @return angle(GPDouble): 
        The computed and rounded angle.
         
    """
    logger.debug("Compute vector b.")
    vector_b_x = point_b_x - point_a_x
    vector_b_y = point_b_y - point_a_y  
    vector_b_z = point_b_z - point_a_z

    logger.debug("Compute vector c.")
    vector_c_x = point_c_x - point_a_x
    vector_c_y = point_c_y - point_a_y  
    vector_c_z = point_c_z - point_a_z

    logger.debug("Compute the angle.")
    cosinus_angle = (
        (vector_b_x*vector_c_x + vector_b_y*vector_c_y + vector_b_z*vector_c_z) 
        / ((math.sqrt(
            math.pow(vector_b_x , 2) + math.pow(vector_b_y , 2) 
            + math.pow(vector_b_z, 2)
            ))
        * (math.sqrt(
            math.pow(vector_c_x , 2) + math.pow(vector_c_y , 2)
            + math.pow(vector_c_z, 2)
            ))) 
        )   
    angle = math.acos(cosinus_angle)
    angle = math.degrees(angle)
    angle = round(angle, 2)

    return angle