"""
Created on 11.07.2017

@author: Matthias Hensen

Create the investigated area as polygon.

function: create_stream_polygon(
    workspace, outer_cross_sections, in_wlb, out_stream_polygon_name)

"""

import logging
import time

import arcpy

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def create_stream_polygon(
        workspace, outer_cross_sections, in_wlb, out_stream_polygon_name):
    """Create the investigated area as polygon.
    
    The polygon is created with the water land border and the outer
    cross sections as boundary lines.
    
    @param workspace(DEWorkspace):
        The workspace for results.
    @param outer_cross_sections(DEFeatureClass): 
        The feature class with the outer cross sections (bounding 
        features).
    @param in_wlb(DEFeatureClass):
        The feature class with the water land border.
    @param out_stream_polygon_name(GPString): 
        The output feature class name.
        
    @return out_stream_polygon(DEFeatureClass):
        The feature class with the water polygon.
    
    """
    logger.info("Start creating stream polygon.")
    try:
        in_features = [outer_cross_sections, in_wlb]
        out_stream_polygon = workspace + "/" + out_stream_polygon_name
        arcpy.FeatureToPolygon_management(in_features, out_stream_polygon)
    except arcpy.ExecuteError:
        logger.warning(
            out_stream_polygon + " already exists. Change output name: " 
            + out_stream_polygon + time.strftime("%d%m%y_%H%M%S")
            )
        out_stream_polygon = (
            out_stream_polygon + time.strftime("%d%m%y_%H%M%S")
            )
        arcpy.FeatureToPolygon_management(in_features, out_stream_polygon)
    logger.info("Creating stream polygon finished successfully.")
    
    return out_stream_polygon