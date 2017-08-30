"""
Created on 20.07.2017

@author: Matthias Hensen

Create the digital terrain model of the watercourse.

function: create_dtmw(
    workspace, in_dtm_channel, in_dtm_foreshore, in_stream_polygon, 
    out_dtm_watercourse_name, reduce_point_set, buffer_distance)
    
"""

import logging
import time

import arcpy

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def create_dtmw(
        workspace, in_dtm_channel, in_dtm_foreshore, in_stream_polygon, 
        out_dtm_watercourse_name, reduce_point_set, buffer_distance):
    """Create the digital terrain model of the watercourse.
    
    First, the points of the digital terrain model of the foreshore 
    which are inside the stream polygon are deleted. If reduce_point_set
    is 'True', the point set is reduced in the given buffer distance.
    Afterwards the digital terrain model of the channel and the digital
    terrain model of the foreshore are merged to create the digital 
    terrain model of the watercourse. Finally the coordinates are
    displayed in the output feature class.
    
    @param workspace(DEWorkspace): 
        The workspace for results.
    @param in_dtm_channel(DEFeatureClass): 
        The digital terrain model of the channel feature class.
    @param in_dtm_foreshore(DEFeatureClass): 
        The digital terrain model of the foreshore feature class. 
    @param in_stream_polygon(DEFeatureClass): 
        The stream polygon feature class.           
    @param out_dtm_watercourse_name(GPString): 
        The name of the feature class with the digital terrain model of
        the watercourse.    
    @param reduce_point_set(GPString): 
        Reduce the point set with a buffer?.
    @param buffer_distance(GPDouble): 
        The buffers distance.
        
    @return out_dtm_watercourse(DEFeatureClass):
        The feature class with the digital terrain model of the 
        watercourse.    
         
    """
    logger.debug("Create feature layer 'dtm_foreshore_layer'.")
    dtm_foreshore_layer = "dtm_foreshore_layer"
    arcpy.MakeFeatureLayer_management(in_dtm_foreshore, dtm_foreshore_layer)
    logger.info("Feature layer 'dtm_foreshore_layer' created successfully.")
    
    logger.debug(
        "Delete points of the digital terrain model of the foreshore which "
        "are inside the stream polygon."
        )
    overlap_type = "INTERSECT"
    search_distance = ""
    selection_type = "NEW_SELECTION"
    arcpy.SelectLayerByLocation_management(
        dtm_foreshore_layer, overlap_type, in_stream_polygon, search_distance,
        selection_type
        )
    arcpy.DeleteFeatures_management(dtm_foreshore_layer)
    logger.info(
        "Points of the digital terrain model of the foreshore which are "
        "inside the stream polygon deleted successfully."
        )
    
    if reduce_point_set:
        logger.debug(
            "Reduce point set with a buffer of " + str(buffer_distance) 
            + " meters."
            )
        search_distance = str(buffer_distance) + " Meters"
        invert_spatial_relationship = "INVERT"
        arcpy.SelectLayerByLocation_management(
            dtm_foreshore_layer, overlap_type, in_stream_polygon,
            search_distance, selection_type, invert_spatial_relationship
            )
        arcpy.DeleteFeatures_management(dtm_foreshore_layer)
        logger.debug("Reducing point set finished successfully.")
    
    logger.debug("Delete feature layer 'dtm_foreshore_layer'.")
    arcpy.Delete_management(dtm_foreshore_layer)
    logger.info("Feature layer 'dtm_foreshore_layer' deleted successfully.")
    
    logger.debug(
        "Merge the digital terrain model of the channel and the digital "
        "terrain model of the foreshore and create the digital terrain "
        "model of the watercourse."
        )
    try:
        inputs = [in_dtm_channel, in_dtm_foreshore]
        out_dtm_watercourse = workspace + "/" + out_dtm_watercourse_name
        arcpy.Merge_management(inputs, out_dtm_watercourse) 
        logger.info(
            "Output feature class " + out_dtm_watercourse + " created "
            "successfully."
            )
    except arcpy.ExecuteError:
        logger.warning(
            out_dtm_watercourse + " already exists. Change output name: " 
            + out_dtm_watercourse + time.strftime("%d%m%y_%H%M%S.")
            )
        out_dtm_watercourse = (
            out_dtm_watercourse + time.strftime("%d%m%y_%H%M%S")
            )
        arcpy.Merge_management(inputs, out_dtm_watercourse) 
        logger.info(
            "Output feature class " + out_dtm_watercourse + " created "
            "successfully."
            )
        
    logger.debug("Display Coordinates in the output feature class.")
    arcpy.AddXY_management(out_dtm_watercourse)
    logger.debug(
        "Displaying Coordinates in the output feature class finished "
        "successfully."
        )

    return out_dtm_watercourse