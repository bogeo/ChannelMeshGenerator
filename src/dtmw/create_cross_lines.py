"""
Created on 16.07.2017

@author: Matthias Hensen

Create lines cross to the waters flow direction.

function: create_cross_lines(
    workspace, in_wlb, in_cross_sections, out_wlb_subdivided_name,
    keep_names)
    
"""

import logging
import time

import arcpy

from configuration.configure_logging import create_logger

from mesh.get_element_count import (
    get_element_count_fix, get_element_count_variable, get_ranges)

from other.sort_features import sort_features


logger = logging.getLogger(__name__)
create_logger(logger)


def create_cross_lines(
        workspace, in_cross_sections, in_wlb, distance, out_cross_lines_name,
        element_count_method, remain_percentage):
    """Create lines cross to the waters flow direction.
    
    First, the output feature class is created. The fields SECTIONID and
    INTERMEDIATEID are added to the output feature class. The water land
    border parts are sorted ascending. For each section, the cross lines
    are created individual. The length ratio between the two water land 
    border parts is computed. The longer water land border part gets 
    determined. Then the first section is added to the output as the
    sections first cross line. After that, the distance between the 
    first two cross lines is computed. If the element count method is 
    FIX, the function mesh.get_element_count_fix is used. If the element
    count method is VARIABLE, the function mesh.get_element_count
    _variable is used. Otherwise the distance is the in parameter 
    distance defined value. Then in a while-loop, the further cross 
    lines are created and added to the output. At the beginning of each
    iteration, it is checked if the remain distance is sufficiently 
    (remain percentage to the end of the water land border part) to 
    create a further cross line. This cross line is placed at the half 
    distance between the last cross line and the cross section at the 
    end. Otherwise the while-loop is finished. The distance between 
    successive cross lines is adjusted by the length ratio. The start 
    and end points for the cross line are set as point object on the 
    water land border. The cross line is created as a polyline and added
    to a list. Then the distance to the next cross line is computed. 
    After creating all cross lines for all sections, the last cross 
    section is added as the last cross line. Then the lists are inserted
    into the output feature class.
    
    @param workspace(DEWorkspace): 
        The workspace for results.   
    @param in_cross_sections(DEFeatureClass):
        The cross sections feature class. 
    @param in_wlb(DEFeatureClass): 
        The water land border feature class.
    @param distance(GPDouble): 
        The medium distance between successive cross lines.           
    @param out_cross_lines_name(GPString): 
        The name of the feature class with the cross lines.    
    @param element_count_method(GPString): 
        The method to compute distance with mesh.get_element_count.
    @param remain_percentage(GPLong):
        The percentage value between the current cross line and the 
        cross section at the end which must be reached at least to
        create a further cross line at the half distance.(The half 
        distance between the last cross line and the cross section at 
        the end).
            
    @return out_cross_lines(DEFeatureClass): 
        The output cross lines feature class.
         
    """
    logger.debug("Create output feature class.")
    try: 
        out_path = workspace + "/"
        geometry_type = "POLYLINE"
        template = ""
        has_m = ""
        has_z = "ENABLED"
        desc = arcpy.Describe(in_cross_sections)
        spatial_reference = desc.spatialReference   
        arcpy.CreateFeatureclass_management(
            out_path, out_cross_lines_name, geometry_type, template, has_m,
            has_z, spatial_reference
            )    
    except arcpy.ExecuteError:
        logger.warning(
            out_path + "/" + out_cross_lines_name + " already exists. Change "
            "output name: " + out_path + "/" +  out_cross_lines_name 
            + time.strftime("%d%m%y_%H%M%S.")
            )
        out_cross_lines_name = (
            out_cross_lines_name + time.strftime("%d%m%y_%H%M%S")
            )
        arcpy.CreateFeatureclass_management(
            out_path, out_cross_lines_name, geometry_type, template, has_m,
            has_z, spatial_reference
            )    
    logger.info("Output feature class created successfully.")

    logger.debug("Add a field SECTIONID.")
    out_cross_lines = workspace + "/" + out_cross_lines_name
    field_name = "SECTIONID"
    field_type = "SHORT"
    arcpy.AddField_management(out_cross_lines, field_name, field_type)
    logger.info("Field SECTIONID added successfully.")
    
    logger.debug("Add a field INTERMEDIATEID.")
    field_name = "INTERMEDIATEID"
    arcpy.AddField_management(out_cross_lines, field_name, field_type)
    logger.info("Field INTERMEDIATEID added successfully.")

    logger.debug("Sort water land border parts.")
    sort_fields = [["SECTIONID", "ASCENDING"], ["WLBID", "ASCENDING"]]
    sort_features(in_wlb, sort_fields)
    logger.info("Sorting water land border parts finished successfully.")

    logger.debug("Count cross sections.")
    result = arcpy.GetCount_management(in_cross_sections)
    count_cross_sections = int(result.getOutput(0))
    logger.info("Counting cross sections finished successfully.")

    logger.debug("Start creating cross lines for each section.")
    cross_lines = []
    section_ids = []
    intermediate_ids = []
    points = []
    point_array = arcpy.Array()
    for section in range(1, count_cross_sections):
        logger.debug(
            "Get the two water land border parts for section " + str(section) 
            + "."
            )
        field_names = ["SHAPE@", "SHAPE@LENGTH", "WLBID"]
        where_clause = "SECTIONID = " + str(section)
        wlb_cursor = arcpy.da.SearchCursor(in_wlb, field_names, where_clause)
        for wlb_row in wlb_cursor:
            if wlb_row[2] == 1:
                wlb1 = wlb_row[1]
            else:
                wlb2 = wlb_row[1]
    
        logger.debug("Compute length ratio.")
        ratio = wlb1 / wlb2
        
        logger.debug("Determine longer water land border part.")
        if wlb1 >= wlb2:
            length_wlb = wlb1
        else:
            length_wlb = wlb2
    
        logger.debug("Reset wlb_cursor.")
        wlb_cursor.reset()
        
        logger.debug("Append cross section as first cross line to the output.")
        field_names = ["SHAPE@LENGTH", "SHAPE@"]
        where_clause = "SECTIONID = " + str(section)
        cs_cursor = arcpy.da.SearchCursor(
            in_cross_sections, field_names, where_clause
            )
        for cs_row in cs_cursor:
            length_cross_section = cs_row[0]
            cross_lines.append(cs_row[1])
            section_ids.append(section)
            intermediate_ids.append(0)
    
        logger.debug("Compute distance between first two cross lines.")
        if element_count_method == "FIX":
            element_count = get_element_count_fix(length_cross_section)
            distance_cross_line = length_cross_section / element_count * 3
        elif element_count_method == "VARIABLE":
            ranges = get_ranges(in_cross_sections)
            element_count = get_element_count_variable(
                length_cross_section, ranges
                )
            distance_cross_line = length_cross_section / element_count * 3
        else:
            distance_cross_line = distance
    
        logger.debug("Set covered distance to length of the first cross line.")
        covered_distance = distance_cross_line
    
        logger.debug(
            "Create the further cross lines in section " + str(section) + "."
            )
        intermediate_id = 1
        while covered_distance < length_wlb:
            if (element_count_method == "FIX"
                    or element_count_method == "VARIABLE"):
                logger.debug("Adjust distance at the end of a section.")
                remain_factor = remain_percentage / 100.0  
                remain_distance = length_wlb - covered_distance
                multiplied_distance = distance_cross_line * remain_factor    
                if (distance_cross_line >= remain_distance 
                        and multiplied_distance > remain_distance):
                    logger.debug(
                        "Break while loop. No further cross line created."
                        )
                    break
                elif (distance_cross_line >= remain_distance 
                        and multiplied_distance <= remain_distance):
                    logger.debug(
                        "Create cross line halfway of the remain distance."
                        )
                    covered_distance = (
                    covered_distance - distance_cross_line
                    + (distance_cross_line+remain_distance) / 2.0      
                    )  
                
            logger.debug("Get start point and end point of the cross line.")
            for wlb_row in wlb_cursor:
                if wlb_row[2] == 1 and ratio >= 1:
                    points.append(
                        wlb_row[0].positionAlongLine(covered_distance)
                        )
                elif wlb_row[2] == 1 and ratio < 1:
                    points.append(
                        wlb_row[0].positionAlongLine(covered_distance * ratio)
                        )
                elif wlb_row[2] == 2 and ratio <= 1:
                    points.append(
                        wlb_row[0].positionAlongLine(covered_distance)
                        )
                elif wlb_row[2] == 2 and ratio > 1:
                    points.append(
                        wlb_row[0].positionAlongLine(covered_distance / ratio)
                        )    
        
            logger.debug("Add start point and end point to a point array.")
            point_array.add(points[0].getPart(0)) 
            point_array.add(points[1].getPart(0)) 
        
            logger.debug("Create cross line from start point and end point.")
            cross_line = arcpy.Polyline(point_array)
        
            logger.debug("Append cross line to the output.")
            cross_lines.append(cross_line)
            section_ids.append(section)
            intermediate_ids.append(intermediate_id)
        
            if (element_count_method == "FIX" 
                    or element_count_method == "VARIABLE"):
                length_cross_line = cross_line.getLength("PLANAR", "METERS") 
                if element_count_method == "FIX":
                    logger.debug(
                        "Compute the distance to the next cross line with "
                        "'get_element_count_fix'."
                        )
                    element_count = get_element_count_fix(length_cross_line)
                elif element_count_method == "VARIABLE":
                    logger.debug(
                        "Compute the distance to the next cross line with "
                        " 'get_element_count_variable'."
                        )
                    element_count = get_element_count_variable(
                        length_cross_line, ranges
                        )
                distance_cross_line = length_cross_section / element_count * 3
        
            logger.debug("Remove all points from 'points' and 'point_array'.")
            del points[:]
            point_array.removeAll()
            
            logger.debug("Reset wlb_cursor.")
            wlb_cursor.reset()
        
            logger.debug("Set covered distance for the next iteration.")
            covered_distance = covered_distance + distance_cross_line
            intermediate_id = intermediate_id + 1  

        logger.debug("Section " + str(section) + " completed.")
   
    logger.debug("Add last cross line (last cross section) to the output.")
    field_names = ["SHAPE@"]
    where_clause = "SECTIONID = " + str(count_cross_sections) 
    cs_cursor = arcpy.da.SearchCursor(
        in_cross_sections, field_names, where_clause
        )
    for cs_row in cs_cursor:
        cross_lines.append(cs_row[0])
        section_ids.append(count_cross_sections)
        intermediate_ids.append(0)

    logger.debug("Insert cross lines to the output feature class.")
    field_names = ["SHAPE@", "SECTIONID", "INTERMEDIATEID"]
    with arcpy.da.InsertCursor(out_cross_lines, field_names) as cursor:
        for i in range(len(cross_lines)):
            cursor.insertRow(
                (cross_lines[i], section_ids[i], intermediate_ids[i])
                )
    logger.info(
        "Cross lines inserted successfully to the output feature class."
        )
    
    return out_cross_lines