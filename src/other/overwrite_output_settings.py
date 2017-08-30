"""
Created on 06.07.2017

@author: Matthias Hensen

Set the env.overwriteOutput parameter.

function overwrite_output_settings(overwrite_output)

"""

import logging

from arcpy import env

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def overwrite_output_settings(overwrite_output):
    """Set overwrite output.
    
    If overwrite_output is 'True', env.overwriteOutput is set to 'True',
    else overwrite_output is set to 'False'.
    
    @param overwrite_output (Boolean):
        Overwrite output? 
    
    """
    if (overwrite_output and not env.overwriteOutput):
        logger.debug("Set overwrite output to 'True'.")
        env.overwriteOutput = True
        logger.info("Overwrite output was set to 'True'.")
        return
    elif (not overwrite_output and env.overwriteOutput):
        logger.debug("Set overwrite output to 'False'.")
        env.overwriteOutput = False
        logger.info("Overwrite output was set to 'False'.")
        return 