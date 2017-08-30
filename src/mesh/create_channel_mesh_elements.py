"""
Created on 23.07.2017

@author: Matthias Hensen

Create the elements for the channel mesh.

function: create_channel_mesh_elements(
    workspace, in_vertices, out_channel_mesh_elements_name)
    
function: create_rectangle(v1, v2, v3, v4),
          
function: create_triangle(v1, v2, v3)
    
"""

import logging
import sys
import time

import arcpy

from configuration.configure_logging import create_logger

from other.sort_features import sort_features


logger = logging.getLogger(__name__)
create_logger(logger)


def create_channel_mesh_elements(
        workspace, in_vertices, out_channel_mesh_elements_name):
    """Create the elements for the channel mesh.
    
    First, the output feature class is created. The fields SECTIONID,
    INTERMEDIATEID and ELEMENTID are added to this feature class. Then 
    the vertices are sorted by SECTIONID, INTERMEDIATEID and VERTEXID.
    A feature layer is created and the number of cross lines is counted.
    Then in each case the both successive cross lines are selected. The
    first cross line is the front cross line and the second cross line 
    is the back cross line. The vertices which are located on the front
    cross line are added to the list front_points and the vertices which
    are located on the back cross line are added to the list 
    back_points. The count of vertices from the first lists is compared 
    with the count of the vertices from the second list. If the count 
    is equal for both lists, (count - 1) rectangles are created between 
    the two cross lines. If the difference is 1, (count - 2) rectangles 
    (seen from the larger list) and a central triangle are created. If 
    the difference is 2, (count - 3) rectangles (seen from the larger 
    list) and a triangle as the second element of each side are created. 
    Each element is appended to a list. After all channel mesh elements 
    are created, they are inserted to the output feature class and
    height (z) information are displayed to the output. Finally the 
    feature layer is deleted.
    
    @param workspace(DEWorkspace): 
        The workspace for results. 
    @param in_vertices(DEFeatureClass):
        The vertices feature class.            
    @param out_channel_mesh_elements_name(GPString): 
        The name of the feature class with the channel mesh elements.
            
    @return out_channel_mesh_elements(DEFeatureClass): 
        The output channel mesh elements feature class.
         
    """
    logger.debug("Create output feature class.")
    try: 
        out_path = workspace + "/"
        geometry_type = "POLYGON"
        template = ""
        has_m = ""
        has_z = "ENABLED"
        desc = arcpy.Describe(in_vertices)
        spatial_reference = desc.spatialReference   
        arcpy.CreateFeatureclass_management(
            out_path, out_channel_mesh_elements_name, geometry_type, template,
            has_m,has_z, spatial_reference
            )    
    except arcpy.ExecuteError:
        logger.warning(
            out_path + "/" + out_channel_mesh_elements_name + " already "
            "exists. Change output name: " + out_path + "/" 
            +  out_channel_mesh_elements_name + time.strftime("%d%m%y_%H%M%S.")
            )
        out_channel_mesh_elements_name = (
            out_channel_mesh_elements_name + time.strftime("%d%m%y_%H%M%S")
            )
        arcpy.CreateFeatureclass_management(
            out_path, out_channel_mesh_elements_name, geometry_type, template,
            has_m, has_z, spatial_reference
            )    
    logger.info("Output feature class created successfully.")    
    
    logger.debug("Add a field SECTIONID.")
    out_channel_mesh_elements = (
        workspace + "/" + out_channel_mesh_elements_name
        )
    field_name = "SECTIONID"
    field_type = "SHORT"
    arcpy.AddField_management(
        out_channel_mesh_elements, field_name, field_type
        )
    logger.info("Field SECTIONID added successfully.")
    
    logger.debug("Add a field INTERMEDIATEID.")
    field_name = "INTERMEDIATEID"
    arcpy.AddField_management(
        out_channel_mesh_elements, field_name, field_type
        )
    logger.info("Field INTERMEDIATEID added successfully.")

    logger.debug("Add a field ELEMENTID.")
    field_name = "ELEMENTID"
    arcpy.AddField_management(
        out_channel_mesh_elements, field_name, field_type
        ) 
    logger.info("Field ELEMENTID added successfully.")
    
    logger.debug("Sort vertices.")
    sort_fields = [
        ["SECTIONID", "ASCENDING"], ["INTERMEDIATEID", "ASCENDING"],
        ["VERTEXID", "ASCENDING"]
        ]
    sort_features(in_vertices, sort_fields)
    logger.info("Sorting vertices finished successfully.")    
    
    logger.debug("Create feature layer 'vertices_layer'.")
    vertices_layer = "vertices_layer"
    arcpy.MakeFeatureLayer_management(in_vertices, vertices_layer)
    logger.info("Feature layer 'vertices_layer' created successfully.")
    
    logger.debug("Count cross lines.")
    selection_type = "NEW_SELECTION"
    where_clause = "VERTEXID = 1"    
    arcpy.SelectLayerByAttribute_management(
        vertices_layer, selection_type, where_clause
        )
    result = arcpy.GetCount_management(vertices_layer)
    count_cross_lines = int(result.getOutput(0))
    logger.info("Counting cross lines finished successfully.")
    
    logger.debug("Start creating channel mesh elements.")
    i = 1
    section = 1
    intermediate = 1
    front_points = []
    back_points = []
    channel_mesh_elements = []
    section_ids = []
    intermediate_ids = []
    element_ids = []
    change_section = False
    while i < count_cross_lines:
        intermediate = intermediate - 1
        for j in range (2):
            logger.debug("Select vertices from successive cross lines.")
            where_clause = (
                "SECTIONID = " + str(section) + " AND INTERMEDIATEID = " 
                + str(intermediate)
                )
            arcpy.SelectLayerByAttribute_management(
                vertices_layer, selection_type, where_clause
                )
            
            logger.debug(
                "Check if vertices are selected correctly. If count_vertices "
                "is 0, adjust the selection at the transition between two "
                "sections."
                )
            result = arcpy.GetCount_management(vertices_layer)
            count_vertices = int(result.getOutput(0))
            if count_vertices == 0:
                change_section = True
                where_clause = (
                    "SECTIONID = " + str(section + 1) + " AND INTERMEDIATEID "
                    "= 0"
                    )
                arcpy.SelectLayerByAttribute_management(
                    vertices_layer, selection_type, where_clause
                    )
        
            logger.debug(
                "Append the points which are located on the cross lines to "
                "the lists front_points or back_points."
                )
            field_names = ["SHAPE@"]
            cursor = arcpy.da.SearchCursor(vertices_layer, field_names)
            for row in cursor:
                if j == 0: 
                    front_points.append(row[0])
                else:
                    back_points.append(row[0])
                    
            intermediate = intermediate + 1
    
        logger.debug("Count front_points and back_points.")
        count_front_points = len(front_points)
        count_back_points = len(back_points)
    
        if count_front_points == count_back_points:
            logger.debug(
                "Count front_points is equal to count back_points. Create "
                + str(count_front_points - 1) + " rectangles."
                )   
            for k in range(count_front_points - 1):
                v1 = front_points[k].firstPoint
                v2 = front_points[k + 1].firstPoint
                v3 = back_points[k + 1].firstPoint
                v4 = back_points[k].firstPoint
                rectangle = create_rectangle(v1, v2, v3, v4)
                channel_mesh_elements.append(rectangle) 
                section_ids.append(section)
                intermediate_ids.append(intermediate - 2)
                element_ids.append(k + 1)
        elif count_front_points == count_back_points + 1:
            logger.debug(
                "Count front_points is greater by 1 than count back_points. "
                "Create " + str(count_front_points - 2) + " rectangles and a "
                "central triangle."
                )
            for k in range(count_front_points - 2):
                if k < (count_front_points/2 - 1):
                    v1 = front_points[k].firstPoint
                    v2 = front_points[k + 1].firstPoint
                    v3 = back_points[k + 1].firstPoint
                    v4 = back_points[k].firstPoint
                    element_ids.append(k + 1)    
                elif k >= (count_front_points/2 - 1):
                    v1 = front_points[k + 1].firstPoint
                    v2 = front_points[k + 2].firstPoint
                    v3 = back_points[k + 1].firstPoint
                    v4 = back_points[k].firstPoint
                    element_ids.append(k + 2)
                rectangle = create_rectangle(v1, v2, v3, v4)
                channel_mesh_elements.append(rectangle) 
                section_ids.append(section)
                intermediate_ids.append(intermediate - 2)
                if k == (count_front_points/2 - 1):
                    v1 = front_points[k].firstPoint
                    v2 = front_points[k + 1].firstPoint
                    v3 = back_points[k].firstPoint
                    triangle = create_triangle(v1, v2, v3)
                    channel_mesh_elements.append(triangle) 
                    section_ids.append(section)
                    intermediate_ids.append(intermediate - 2)
                    element_ids.append(k + 1)
        elif count_front_points + 1 == count_back_points:
            logger.debug(
                "Count front_points is smaller by 1 than count back_points. "
                "Create " + str(count_back_points - 2) + " rectangles and a "
                "central triangle."
                )            
            for k in range(count_back_points - 2):
                if k < (count_front_points / 2):
                    v1 = front_points[k].firstPoint
                    v2 = front_points[k + 1].firstPoint
                    v3 = back_points[k + 1].firstPoint
                    v4 = back_points[k].firstPoint 
                    element_ids.append(k + 1)   
                elif k >= (count_front_points / 2):
                    v1 = front_points[k].firstPoint
                    v2 = front_points[k + 1].firstPoint
                    v3 = back_points[k + 2].firstPoint
                    v4 = back_points[k + 1].firstPoint
                    element_ids.append(k + 2)
                rectangle = create_rectangle(v1, v2, v3, v4)
                channel_mesh_elements.append(rectangle) 
                section_ids.append(section)
                intermediate_ids.append(intermediate - 2)
                if k == (count_front_points / 2):
                    v1 = front_points[k].firstPoint
                    v2 = back_points[k + 1].firstPoint
                    v3 = back_points[k].firstPoint
                    triangle = create_triangle(v1, v2, v3)
                    channel_mesh_elements.append(triangle) 
                    section_ids.append(section)
                    intermediate_ids.append(intermediate - 2)
                    element_ids.append(k + 1)
        elif count_front_points == count_back_points + 2:
            logger.debug(
                "Count front_points is greater by 2 than count back_points. "
                "Create " + str(count_front_points - 3) + " rectangles and a "
                "triangle as second element on each side."
                )
            for k in range(count_front_points - 1):
                if k == 0:
                    v1 = front_points[k].firstPoint
                    v2 = front_points[k + 1].firstPoint
                    v3 = back_points[k + 1].firstPoint
                    v4 = back_points[k].firstPoint
                    rectangle = create_rectangle(v1, v2, v3, v4)
                    channel_mesh_elements.append(rectangle) 
                    section_ids.append(section)
                    intermediate_ids.append(intermediate - 2)
                    element_ids.append(k + 1)
                elif (k > 1 and k < (count_front_points - 3)):
                    v1 = front_points[k].firstPoint
                    v2 = front_points[k + 1].firstPoint
                    v3 = back_points[k].firstPoint
                    v4 = back_points[k - 1].firstPoint
                    rectangle = create_rectangle(v1, v2, v3, v4)
                    channel_mesh_elements.append(rectangle) 
                    section_ids.append(section)
                    intermediate_ids.append(intermediate - 2)
                    element_ids.append(k + 1)   
                elif k == (count_front_points - 2):
                    v1 = front_points[k].firstPoint
                    v2 = front_points[k + 1].firstPoint
                    v3 = back_points[k - 1].firstPoint
                    v4 = back_points[k - 2].firstPoint
                    rectangle = create_rectangle(v1, v2, v3, v4)
                    channel_mesh_elements.append(rectangle) 
                    section_ids.append(section)
                    intermediate_ids.append(intermediate - 2)
                    element_ids.append(k + 1)
                if k == 1:
                    v1 = front_points[k].firstPoint
                    v2 = front_points[k + 1].firstPoint
                    v3 = back_points[k].firstPoint
                    triangle = create_triangle(v1, v2, v3)
                    channel_mesh_elements.append(triangle) 
                    section_ids.append(section)
                    intermediate_ids.append(intermediate - 2)
                    element_ids.append(k + 1)
                elif k == (count_front_points - 3):
                    v1 = front_points[k].firstPoint
                    v2 = front_points[k + 1].firstPoint
                    v3 = back_points[k - 1].firstPoint
                    triangle = create_triangle(v1, v2, v3)
                    channel_mesh_elements.append(triangle) 
                    section_ids.append(section)
                    intermediate_ids.append(intermediate - 2)
                    element_ids.append(k + 1)
        elif count_front_points + 2 == count_back_points:
            logger.debug(
                "Count front_points is smaller by 2 than count back_points. "
                "Create " + str(count_back_points - 3) + " rectangles and a "
                "triangle as second element on each side."
                )            
            for k in range(count_front_points + 2):
                if k == 0:
                    v1 = front_points[k].firstPoint
                    v2 = front_points[k + 1].firstPoint
                    v3 = back_points[k + 1].firstPoint
                    v4 = back_points[k].firstPoint
                    rectangle = create_rectangle(v1, v2, v3, v4)
                    channel_mesh_elements.append(rectangle) 
                    section_ids.append(section)
                    intermediate_ids.append(intermediate - 2)
                    element_ids.append(k + 1)
                elif (k > 0 and k < (count_front_points - 2)):
                    v1 = front_points[k].firstPoint
                    v2 = front_points[k + 1].firstPoint
                    v3 = back_points[k + 2].firstPoint
                    v4 = back_points[k + 1].firstPoint
                    rectangle = create_rectangle(v1, v2, v3, v4)
                    channel_mesh_elements.append(rectangle) 
                    section_ids.append(section)
                    intermediate_ids.append(intermediate - 2)
                    element_ids.append(k + 2)    
                elif k == (count_front_points - 2):
                    v1 = front_points[k].firstPoint
                    v2 = front_points[k + 1].firstPoint
                    v3 = back_points[k + 3].firstPoint
                    v4 = back_points[k + 2].firstPoint
                    rectangle = create_rectangle(v1, v2, v3, v4)
                    channel_mesh_elements.append(rectangle) 
                    section_ids.append(section)
                    intermediate_ids.append(intermediate - 2)
                    element_ids.append(k + 3)
                if k == 1:
                    v1 = front_points[k].firstPoint
                    v2 = back_points[k + 1].firstPoint
                    v3 = back_points[k].firstPoint
                    triangle = create_triangle(v1, v2, v3)
                    channel_mesh_elements.append(triangle) 
                    section_ids.append(section)
                    intermediate_ids.append(intermediate - 2)
                    element_ids.append(k + 1)
                elif k == (count_front_points - 2):
                    v1 = front_points[k].firstPoint
                    v2 = back_points[k + 2].firstPoint
                    v3 = back_points[k + 1].firstPoint 
                    triangle = create_triangle(v1, v2, v3)
                    channel_mesh_elements.append(triangle) 
                    section_ids.append(section)
                    intermediate_ids.append(intermediate - 2)
                    element_ids.append(k + 2)
        
        logger.debug("Empty lists front_points and back_points.")   
        del front_points[:]
        del back_points [:]    
        i = i + 1
        if change_section:
            section = section + 1
            intermediate = 1
            change_section = False
        logger.debug(
            "Channel mesh elements between cross lines " + str(i - 1) + " and "
            + str(i) + " created successfully."
            )    

    logger.debug("Insert elements to the output feature class.")
    field_names = ["SHAPE@", "SECTIONID", "INTERMEDIATEID", "ELEMENTID"]
    with arcpy.da.InsertCursor(
            out_channel_mesh_elements, field_names) as cursor:
        for i in range(len(channel_mesh_elements)):
            cursor.insertRow((
                channel_mesh_elements[i], section_ids[i], intermediate_ids[i],     
                element_ids[i]
                ))    
    logger.info(
        "Elements inserted successfully to the output feature class"
        )

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
    
    logger.debug("Display height (z) information in the output feature class.")
    out_property = [
        "Z_MIN", "Z_MAX", "Z_MEAN", "LENGTH_3D", "VERTEX_COUNT", "MIN_SLOPE",
        "MAX_SLOPE", "AVG_SLOPE"
        ]
    try: 
        arcpy.AddZInformation_3d(out_channel_mesh_elements, out_property) 
        logger.info(
            "Displaying height (z) information in the output feature class "
            "finished successfully."
            )
    except arcpy.ExecuteError:
        logger.error("Displaying height (z) information failed.")
        sys.exit(0)

    arcpy.CheckInExtension("3D")
    
    logger.debug("Delete feature feature layer 'vertices_layer'.")
    arcpy.Delete_management(vertices_layer)
    logger.info("Feature layer 'vertices_layer' deleted successfully.")
    
    return out_channel_mesh_elements


def create_rectangle(v1, v2, v3, v4):
    """Create a rectangle.
    
    An array is created and the four vertices are added to the array. To
    close the polygon, the first vertex is added again at the end. The
    rectangle is created with the points which are in the array.
    
    @param v1(GPPoint): 
        The first vertex. 
    @param v2(GPPoint): 
        The second vertex
    @param v3(GPPoint): 
        The third vertex
    @param v4(GPPoint): 
        The fourth vertex    
            
    @return rectangle(GPPolygon): 
        The output rectangle.
         
    """
    logger.debug("Create rectangle.")
    array = arcpy.Array()
    array.add(v1)
    array.add(v2)
    array.add(v3)
    array.add(v4)
    array.add(v1)
    spatial_reference = False
    has_z = True
    rectangle = arcpy.Polygon(array, spatial_reference, has_z)
    
    return rectangle


def create_triangle(v1, v2, v3):
    """Create a triangle.
    
    An array is created and the three vertices are added to the array. 
    To close the polygon, the first vertex is added again at the end. 
    The triangle is created with the points which are in the array.
    
    @param v1(GPPoint): 
        The first vertex. 
    @param v2(GPPoint): 
        The second vertex
    @param v3(GPPoint): 
        The third vertex

    @return triangle(GPPolygon): 
        The output rectangle.
         
    """
    logger.debug("Create triangle.")
    array = arcpy.Array()
    array.add(v1)
    array.add(v2)
    array.add(v3)
    array.add(v1)
    spatial_reference = False
    has_z = True
    triangle = arcpy.Polygon(array, spatial_reference, has_z)
    
    return triangle
