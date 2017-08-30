"""
Created on 06.07.2017

@author: Matthias Hensen

Load points from .csv, .txt or .xyz files to a feature class.

function: load_points(
    workspace, in_points, out_points_name, spatial_reference, 
    in_x_field, in_y_field, in_z_field, decimal_separator)
    
function: load_points_from_multiple_files(
    workspace, in_point_files, out_points_name, spatial_reference, 
    in_x_field, in_y_field, in_z_field, decimal_separator)


"""

import logging
import sys
import time

import arcpy

from configuration.configure_logging import create_logger

from other.list_field_names import list_field_names


logger = logging.getLogger(__name__)
create_logger(logger)

    
def load_points(
        workspace, in_points, out_points_name, spatial_reference, in_x_field,
        in_y_field, in_z_field, decimal_separator):
    """Load points from a csv, txt or xyz file to a feature class.
    
    First, the spatial reference object is created. After that, it is 
    checked if the input type is csv or txt or xyz. If the input type
    is csv or txt, it is created a XYEventLayer which gets copied as
    a feature class. In this case, it is important, that the x, y and z
    fields exist. If the input type is xyz, the function
    ASCII3DToFeatureClass_3d is called which creates the feature class
    automatically.
    
    @param workspace(DEWorkspace):
        The workspace for results.
    @param in_points(DEFile):
        The file with the input points.
    @param out_points_name(GPString): 
        The output feature class name.
    @param spatial_reference(item):
        The item (epsg or name) for the spatial reference object which
        will be created.
    @param in_x_field(GPString)
        The input x field.
    @param in_y_field(GPString)
        The input y field.
    @param in_z_field(GPString)
        The input z field.
    @param decimal_separator(GPString)
        The decimal separator for xyz files.
            
    @return out_points(DEFeatureClass):
        The output feature class.
    
    """ 
    logger.debug(
        "Set spatial reference with the name: " + str(spatial_reference) + "."
        )
    spatial_reference = arcpy.SpatialReference(spatial_reference)
    logger.info("Generating spatial reference completed successfully.")
    
    desc = arcpy.Describe(in_points)
    logger.debug("The data type of in_points is: " + str(desc.extension))
    
    if desc.extension == "csv" or desc.extension == "txt":
        logger.debug("Check if x_field, y_field and z_field exist.")
        field_names = list_field_names(in_points)
        try:
            if (in_x_field not in field_names or in_y_field not in field_names
                    or in_z_field not in field_names):
                logger.error("input fields do not exist. Execution failed.")
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            sys.exit(0)

        logger.debug("Make XYEventLayer.")
        event_layer = "xy_temp"
        arcpy.MakeXYEventLayer_management(
            in_points, in_x_field, in_y_field, event_layer, spatial_reference,
            in_z_field)
        logger.info("XYEventLayer " + event_layer + " created successfully.")
    
        logger.debug("Save " + event_layer + " as feature class.")
        try:
            out_points = workspace + "/" + out_points_name
            arcpy.CopyFeatures_management(event_layer, out_points)
        except arcpy.ExecuteError:
            logger.warning(
                out_points + " already exists. Change output name: " 
                + out_points + time.strftime("%d%m%y_%H%M%S.")
                )
            out_points = out_points + time.strftime("%d%m%y_%H%M%S")
            arcpy.CopyFeatures_management(event_layer, out_points)   
        logger.info("Feature class " + out_points + " created successfully.")
        
        logger.debug("Delete event layer '" + event_layer + "'.")
        arcpy.Delete_management(event_layer)
        logger.info("'" + event_layer + "' deleted successfully.")
        
        return out_points
      
    elif desc.extension == "xyz": 
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
        
        logger.debug("Create feature class from xyz file.") 
        try:
            in_file_type = "XYZ"
            out_points = workspace + "/" + out_points_name
            out_geometry_type = "POINT"
            z_factor = ""
            average_point_spacing = ""
            file_suffix = "XYZ"
            arcpy.ASCII3DToFeatureClass_3d(
                in_points, in_file_type, out_points, out_geometry_type,
                z_factor, spatial_reference, average_point_spacing,
                file_suffix, decimal_separator)
        except arcpy.ExecuteError:
            logger.warning(
                out_points + "already exists. Change output name: " 
                + out_points + time.strftime("%d%m%y_%H%M%S")
                )
            out_points = out_points + time.strftime("%d%m%y_%H%M%S")
            arcpy.ASCII3DToFeatureClass_3d(
                in_points, in_file_type, out_points, out_geometry_type,
                z_factor, spatial_reference, average_point_spacing,
                file_suffix, decimal_separator)
        logger.info("Feature class " + out_points + " created successfully.")
        
        arcpy.CheckInExtension("3D")
        
        return out_points


def load_points_from_multiple_files(
        workspace, in_point_files, out_points_name, spatial_reference, 
        in_x_field, in_y_field, in_z_field, decimal_separator):
    """Load points from multiple files to a feature class.
    
    For each input file the function load_points is called and executed.
    The point files are merged to the output feature class. The single
    point feature classes are deleted.
    
    @param workspace(DEWorkspace):
        The workspace for results.
    @param in_point_files(DEFile):
        The files with the input points.
    @param out_points_name(GPString): 
        The output feature class name.
    @param spatial_reference(item):
        The item (epsg or name) for the spatial reference object which
        will be created.
    @param in_x_field(GPString)
        The input x field.
    @param in_y_field(GPString)
        The input y field.
    @param in_z_field(GPString)
        The input z field.
    @param decimal_separator(GPString)
        The decimal separator for xyz files.
            
    @return out_points(DEFeatureClass):
        The output feature class.
    
    """ 
    logger.debug("Split the input point files.")
    in_point_files = in_point_files.split(";")
    logger.info("Splitting input files finished successfully.")
    count_files = 1
    point_feature_classes = []
    for in_file in in_point_files:
        logger.info(
        "Start function load_points to load the points from the input files. "
        "The current input file is: " + in_file
        )
        try:
            in_points = load_points(
                workspace, in_file, out_points_name + str(count_files), 
                spatial_reference, in_x_field, in_y_field, in_z_field, 
                decimal_separator
                )
        except arcpy.ExecuteError:
            logger.warning(
                out_points_name + str(count_files) + "already exists. Change "
                "name to " + out_points_name + "m_in_file_" + str(count_files)
                + " and delete a same-named file if necessary.")
            if arcpy.Exists(out_points_name + "m_in_file_" + str(count_files)):
                arcpy.Delete_management(out_points_name + "m_in_file_" 
                    + str(count_files)
                    )
            in_points = load_points(
                workspace, in_file, out_points_name + "m_in_file_"
                + str(count_files), spatial_reference, in_x_field, in_y_field,
                in_z_field, decimal_separator
                )
        point_feature_classes.append(in_points)
        count_files = count_files + 1
        logger.info("Load_points finished successfully.")
                
    logger.debug("Merge point files.")
    try:
        out_points = workspace + "/" + out_points_name   
        arcpy.Merge_management(point_feature_classes, out_points)
    except arcpy.ExecuteError:
        logger.warning(
            out_points + " already exists. Change output name: " + out_points
            + time.strftime("%d%m%y_%H%M%S")
            )
        out_points = out_points + time.strftime("%d%m%y_%H%M%S")
        arcpy.Merge_management(point_feature_classes, out_points)
    logger.info("Merging point files finished successfully.")
            
    logger.debug("Delete the input files.")
    for feature_class in point_feature_classes:
        arcpy.Delete_management(feature_class)
    logger.info("Deleting the input files finished successfully.")
    
    return out_points