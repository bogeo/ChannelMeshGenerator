"""
Created on 22.07.2017

@author: Matthias Hensen

Create a triangulated irregular network.

function: create_tin (
    in_tin_points, out_directory, out_tin_name, triangulation_technique)
    
"""

import logging
import sys
import time

import arcpy

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def create_tin(
        in_tin_points, out_directory, out_tin_name, triangulation_technique):
    """Create a triangulated irregular network.
    
    The triangulated irregular network is created in the output directory.
    
    @param in_tin_points(DEFeatureClass):
        The input points which are used to create a triangulated 
        irregular network.
    @param out_directory(DEFolder):
        The output directory.
    @param out_tin_name(GPString):
        The name of the output triangulated irregular network. 
    @param triangulation_technique(GPStrin):
        The triangulation technique used along breaklines.       
            
    @return out_tin(DETin): 
        The output triangulated irregular network.
         
    """
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
    
    logger.debug("Create triangulated irregular network.")
    folder_name = "tin"
    arcpy.CreateFolder_management(out_directory, folder_name)
    try: 
        desc = arcpy.Describe(in_tin_points)
        spatial_reference = desc.spatialReference   
        out_tin = out_directory + "/" + folder_name + "/" + out_tin_name
        arcpy.CreateTin_3d(
            out_tin, spatial_reference, in_tin_points, triangulation_technique
            )
    except arcpy.ExecuteError:
        logger.warning(
            "Output tin " + out_tin + "already exists. Change output "
                "folder: " + folder_name + time.strftime("%d%m%y_%H%M%S")
                )
        folder_name = folder_name + time.strftime("%d%m%y_%H%M%S")
        arcpy.CreateFolder_management(out_directory, folder_name) 
        out_tin = out_directory + "/" + folder_name + "/" + out_tin_name
        arcpy.CreateTin_3d(
            out_tin, spatial_reference, in_tin_points, triangulation_technique
            )   
    logger.info(
        "Creating triangulated irregular network finished successfully."
        )
    
    arcpy.CheckInExtension("3D")
    
    return out_tin
    