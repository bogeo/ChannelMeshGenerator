"""
Created on 15.07.2017

@author: Matthias Hensen

Create a specific count of longitudinal sections.

function: create_longitudinal_sections(
    workspace, in_intermediate_cross_sections, 
    count_longitudinal_sections, out_longitudinal_section_points_name, 
    out_longitudinal_section_lines_name)
    
"""

import logging
import time

import arcpy
from arcpy import env

from configuration.configure_logging import create_logger

from other.sort_features import sort_features


logger = logging.getLogger(__name__)
create_logger(logger)


def create_longitudinal_sections(
        workspace, in_intermediate_cross_sections, count_longitudinal_sections,
        out_longitudinal_section_points_name, 
        out_longitudinal_section_lines_name):
    """Create a specific count of longitudinal sections.
    
    First, the outputZFlag is set to 'Enabled' and the default
    outputZValue is set to '0'. Then the percentage value is formatted.
    The determined count of longitudinal section points is created on
    each cross section and intermediate cross section. Afterwards, it is
    checked if duplicated points exist caused by rounding errors. Then a
    field POINTID is added which is used as line field. The longitudinal
    section points are connected to lines.
    
    @param workspace(DEWorkspace): 
        The workspace for results.
    @param in_intermediate_cross_sections(DEFeatureClass): 
        The intermediate cross sections feature class.    
    @param count_longitudinal_sections(GPLong): 
        The count of longitudinal sections which should be created.    
    @param out_longitudinal_section_points_name(GPString): 
        The name of the feature class with the longitudinal section 
        points.    
    @param out_longitudinal_section_lines_name(GPString): 
        The name of the feature class with the longitudinal section 
        lines.
        
    @return out_longitudinal_sections(List):
        The longitudinal section points and lines feature classes.    
         
    """
    env.outputZFlag = "Enabled"
    env.outputZValue = 0
    
    logger.debug("Start formatting the percentage value.")
    percentage_unformatted = str(1.0 / (count_longitudinal_sections - 1) * 100)
    percentage_formatted = str.replace(percentage_unformatted, ".", ",")
    logger.info("Formatting percentage value finished successfully.")

    logger.debug("Create the longitudinal section points.")
    try:
        out_longitudinal_section_points = (
            workspace + "/" + out_longitudinal_section_points_name
            )
        point_placement = "PERCENTAGE"
        distance = ""
        include_end_points = "END_POINTS"
        arcpy.GeneratePointsAlongLines_management(
            in_intermediate_cross_sections, out_longitudinal_section_points,
            point_placement, distance, percentage_formatted, include_end_points
            )
    except arcpy.ExecuteError:
        logger.warning(
            out_longitudinal_section_points + " already exists. Change output "
            "name: " + out_longitudinal_section_points 
            + time.strftime("%d%m%y_%H%M%S.")
            )
        out_longitudinal_section_points = (
            out_longitudinal_section_points + time.strftime("%d%m%y_%H%M%S")
            )
        arcpy.GeneratePointsAlongLines_management(
            in_intermediate_cross_sections, out_longitudinal_section_points,
            point_placement, distance, percentage_formatted, include_end_points
            )    
    logger.info("Longitudinal section points created successfully.")

    logger.debug("Check if duplicated points exist and delete them. ")
    fields = "Shape"
    xy_tolerance = "1 Centimeters"
    arcpy.DeleteIdentical_management (
        out_longitudinal_section_points, fields, xy_tolerance
        )
    
    logger.debug("Add a field POINTID.")
    field_name = "POINTID"
    field_type = "SHORT"
    arcpy.AddField_management(
        out_longitudinal_section_points, field_name, field_type
        )
    logger.info("Field POINTID added successfully.")

    logger.debug(
        "Create cursor for allocating the POINTIDs from 1 - "
        + str(count_longitudinal_sections) + "."
        )
    field_names = ["POINTID"]
    with arcpy.da.UpdateCursor(
            out_longitudinal_section_points, field_names) as cursor:
        i = 1
        for row in cursor:
            row[0] = i
            cursor.updateRow(row)
            i = i + 1
            if i > count_longitudinal_sections:
                i = 1
    logger.info("Set POINTID successfully.")
    
    logger.debug("Sort longitudinal section points.")
    sort_fields = [
        ["SECTIONID", "ASCENDING"], ["INTERMEDIATEID", "ASCENDING"],
        ["POINTID", "ASCENDING"]
        ]
    sort_features(out_longitudinal_section_points, sort_fields)
    logger.info("Sorting longitudinal section points finished successfully.")
    
    logger.debug("Connect longitudinal sections.")
    try:       
        out_longitudinal_section_lines = (
            workspace + "/" + out_longitudinal_section_lines_name
            )
        line_field = "POINTID"
        arcpy.PointsToLine_management(
            out_longitudinal_section_points, out_longitudinal_section_lines,
            line_field
            )
    except arcpy.ExecuteError:
        logger.warning(
            out_longitudinal_section_lines + " already exists. Change output "
            "name: " + out_longitudinal_section_lines 
            + time.strftime("%d%m%y_%H%M%S.")
            )
        out_longitudinal_section_lines = (
            out_longitudinal_section_lines + time.strftime("%d%m%y_%H%M%S")
            )
        arcpy.PointsToLine_management(
            out_longitudinal_section_points, out_longitudinal_section_lines,
            line_field
            )    
    logger.info("Longitudinal section lines connected successfully.")
    
    return [out_longitudinal_section_points, out_longitudinal_section_lines]