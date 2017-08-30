"""
Created on 11.07.2017

@author: Matthias Hensen

Create the center line of a stream.

function: create_stream_center_line(
    workspace, in_wlb, out_stream_center_line_name)

"""

import logging
import time

import arcpy

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def create_stream_center_line(workspace, in_wlb, out_stream_center_line_name):
    """Create the center line of a stream.
    
    @param workspace(DEWorkspace): 
        The workspace for results.
    @param in_wlb(DEFeatureClass): 
        The feature class with the water land border.
    @param out_stream_center_line_name(GPString): 
        The output feature class name.
        
    @return out_stream_center_line(DEFeatureClass):
        The feature class with the stream center line.
    
    """
    logger.debug("Create stream center line " + out_stream_center_line_name)
    try:
        out_stream_center_line = workspace + "/" + out_stream_center_line_name
        maximum_width = "1000 Meters" 
        arcpy.CollapseDualLinesToCenterline_cartography(
            in_wlb, out_stream_center_line, maximum_width
            )
    except arcpy.ExecuteError:
        logger.warning(
            out_stream_center_line + " already exists. Change output name: "
            + out_stream_center_line + time.strftime("%d%m%y_%H%M%S")
            )
        out_stream_center_line = (
            out_stream_center_line + time.strftime("%d%m%y_%H%M%S")
            )
        arcpy.CollapseDualLinesToCenterline_cartography(
            in_wlb, out_stream_center_line, maximum_width
            )
    logger.info(
        "Feature class " + out_stream_center_line + " created successfully."
        )
    
    return out_stream_center_line