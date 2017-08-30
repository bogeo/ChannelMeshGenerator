"""
Created on 22.07.2017

@author: Matthias Hensen

Create the vertices for the channel mesh.

function: create_vertices(
    workspace, in_cross_lines, in_cross_sections, in_tin, 
    out_vertices_name, element_count_method)
    
"""

import logging
import sys
import time

import arcpy

from configuration.configure_logging import create_logger

from mesh.get_element_count import (
    get_element_count_fix, get_element_count_variable, get_ranges)


logger = logging.getLogger(__name__)
create_logger(logger)


def create_vertices(
        workspace, in_cross_lines, in_cross_sections, in_tin,
        out_vertices_name, element_count_method):
    """Create the vertices for the channel mesh.
    
    First, the output feature class is created. The fields SECTIONID,
    INTERMEDIATEID and VERTEXID are added to the output feature class. 
    Then the vertices are created. The element count is depending on the
    element count method. The vertices are inserted into the output
    feature class. The height values are assigned from the input
    triangulated irregular network. Finally the coordinates are 
    displayed at the output.
    
    @param workspace(DEWorkspace): 
        The workspace for results. 
    @param in_cross_lines(DEFeatureClass):
        The cross lines feature class.   
    @param in_cross_sections(DEFeatureClass):
        The cross sections feature class. 
    @param in_tin(DETin): 
        The input triangulated irregular network..           
    @param out_vertices_name(GPString): 
        The name of the feature class with the vertices.    
    @param element_count_method(GPString): 
        The method to compute distance with mesh.get_element_count.
            
    @return out_vertices(DEFeatureClass): 
        The output vertices feature class.
         
    """
    logger.debug("Create output feature class.")
    try: 
        out_path = workspace + "/"
        geometry_type = "POINT"
        template = ""
        has_m = ""
        has_z = "ENABLED"
        desc = arcpy.Describe(in_cross_lines)
        spatial_reference = desc.spatialReference   
        arcpy.CreateFeatureclass_management(
            out_path, out_vertices_name, geometry_type, template, has_m, has_z,
            spatial_reference
            )    
    except arcpy.ExecuteError:
        logger.warning(
            out_path + "/" + out_vertices_name + " already exists. Change "
            "output name: " + out_path + "/" +  out_vertices_name 
            + time.strftime("%d%m%y_%H%M%S.")
            )
        out_vertices_name = out_vertices_name + time.strftime("%d%m%y_%H%M%S")
        arcpy.CreateFeatureclass_management(
            out_path, out_vertices_name, geometry_type, template, has_m, has_z,
            spatial_reference
            )    
    logger.info("Output feature class created successfully.")
    
    logger.debug("Add a field SECTIONID.")
    out_vertices = workspace + "/" + out_vertices_name
    field_name = "SECTIONID"
    field_type = "SHORT"
    arcpy.AddField_management(out_vertices, field_name, field_type)
    logger.info("Field SECTIONID added successfully.")
    
    logger.debug("Add a field INTERMEDIATEID.")
    field_name = "INTERMEDIATEID"
    arcpy.AddField_management(out_vertices, field_name, field_type)
    logger.info("Field INTERMEDIATEID added successfully.")

    logger.debug("Add a field VERTEXID.")
    field_name = "VERTEXID"
    arcpy.AddField_management(out_vertices, field_name, field_type) 
    logger.info("Field VERTEXID added successfully.")
    
    logger.debug("Start creating vertices.")
    if element_count_method == "VARIABLE":
        ranges = get_ranges(in_cross_sections)
    section_ids = []
    intermediate_ids = []
    vertex_ids = []
    vertices = []
    field_names = ["SHAPE@", "SHAPE@LENGTH", "SECTIONID", "INTERMEDIATEID"]
    cursor = arcpy.da.SearchCursor(in_cross_lines, field_names)
    for row in cursor:
        if element_count_method == "FIX":
            element_count = get_element_count_fix(row[1])
        elif element_count_method == "VARIABLE":
            element_count = get_element_count_variable(row[1], ranges)
        part = row[1] / element_count
        covered_distance = 0
        for i in range(element_count + 1):
            vertices.append(row[0].positionAlongLine(covered_distance))
            section_ids.append(row[2])
            intermediate_ids.append(row[3])
            vertex_ids.append(i + 1)
            covered_distance = covered_distance + part
    logger.info("Creating vertices finished successfully.")
    
    logger.debug("Insert vertices to the output feature class.")        
    field_names = ["SHAPE@", "SECTIONID", "INTERMEDIATEID", "VERTEXID"]
    with arcpy.da.InsertCursor(out_vertices, field_names) as cursor:
        for i in range(len(vertices)):
            cursor.insertRow(
                (vertices[i], section_ids[i], intermediate_ids[i],
                vertex_ids[i])
                )
    logger.info("Vertices inserted successfully to output feature class.")   
    
    logger.debug("Start checking out the '3D Analyst' license.")
    try:
        if arcpy.CheckExtension("3D") == "Available":
            arcpy.CheckOutExtension("3D")
        else:
            raise arcpy.ExecuteError
    except arcpy.ExecuteError:
        logger.error("'3D Analyst' license is unavailable")
        sys.exit(0)
    logger.info(
        "Checking out the '3D Analyst' license finished successfully."
        )
    
    logger.debug("Assign height (z) values to 'SHAPE@Z'.")
    out_property = "Z"
    method = "LINEAR"
    arcpy.AddSurfaceInformation_3d(out_vertices, in_tin, out_property, method)
    field_names = ["Z", "SHAPE@Z"]
    with arcpy.da.UpdateCursor(out_vertices, field_names) as cursor:
        for row in cursor:
            row[1] = row[0]
            cursor.updateRow(row)
    logger.info("Height (z) values assigned successfully.") 
    
    arcpy.CheckInExtension("3D")
    
    logger.debug("Display Coordinates in the output feature class.")
    arcpy.AddXY_management(out_vertices)
    logger.info(
        "Displaying Coordinates in the output feature class finished "
        "successfully."
        )
    
    return out_vertices