"""
Created on 11.07.2017

@author: Matthias

List the field names of an input table.

function: list_field_names(in_table)

"""

import logging

import arcpy

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def list_field_names(in_table):
    """List the field names of an input table.
    
    The field names are appended to a list field_names.
    
    @param: in_features(DETable): 
        The input table.
    
    @return field_names(List): 
        List which contains the field names.
    
    """
    fields = arcpy.ListFields(in_table)
    field_names = []
    
    logger.debug("List field names of " + in_table + ".")
    for field in fields:
        field_names.append(field.name)
        
    return field_names