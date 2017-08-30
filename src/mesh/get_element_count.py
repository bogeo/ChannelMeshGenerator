"""
Created on 17.07.2017

@author: Matthias Hensen

Return the element count dependent on the cross lines length.

functions:  get_element_count_fix(length_cross_line),
            get_ranges(in_cross_sections),
            get_element_count_variable(length_cross_line, ranges)
"""

import logging

import arcpy

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def get_element_count_fix(length_cross_line):
    """Return the element count dependent on the cross lines length.
    
    @param length_cross_line(GPDouble):
        The previous cross lines length        
            
    @return element_count(DELong): 
        The element count for the next cross line
         
    """
    if length_cross_line < 7:
        element_count = 3
    elif (length_cross_line >= 7 and length_cross_line < 10):
        element_count = 4
    elif (length_cross_line >= 10 and length_cross_line < 15):
        element_count = 5
    elif (length_cross_line >= 15 and length_cross_line < 21):
        element_count = 6   
    elif (length_cross_line >= 21 and length_cross_line < 70):
        element_count = 6   
        i = 21
        while i <= length_cross_line:
            i = i + 7
            element_count = element_count + 1
    elif length_cross_line >= 70:
        element_count = 14    
    
    logger.debug(
        "returns the number of elements for the next row: "
        + str(element_count) + " elements."
        )
           
    return element_count


def get_ranges(in_cross_sections):
    """Compute the ranges used to get the element count.
    
    The ranges depend on the shortest and longest cross section length.
    
    @param in_cross_sections(DEFeatureClass): 
        The input cross sections feature class.         
            
    @return ranges(list): 
        The ranges used to get the element count.
         
    """
    logger.debug("Determine the shortest and longest cross section length.")
    field_names = ["SHAPE@LENGTH"]
    maximum_length = 0
    minimum_length = 1000
    cursor = arcpy.da.SearchCursor(in_cross_sections, field_names)
    for row in cursor:
        if row[0] > maximum_length:
            maximum_length = row[0]
        if row[0] < minimum_length:
            minimum_length = row[0]
    minimum_length = int(minimum_length - 1)
    maximum_length = int(maximum_length + 1)
    
    logger.debug("Determine the lower and upper bound.")
    ranges = []    
    lower_bound = int(minimum_length - minimum_length*0.2)
    ranges.append(lower_bound)
    upper_bound = int(maximum_length + maximum_length*0.2)
    ranges.append(upper_bound)
    
    logger.debug("Determine the ranges between the lower and upper bound.")
    difference = upper_bound - lower_bound
    range_width = difference / 5
    ranges.append(range_width)
    
    return ranges
    
    
def get_element_count_variable(length_cross_line, ranges):
    """Return the element count dependent on the cross lines length.
    
    The element count depends on the cross lines length and the range
    depends on the shortest and longest cross section length.
    
    @param length_cross_line(GPDouble): 
        The previous cross lines length.
    @param ranges(list): 
        The ranges used to get the element count.          
            
    @return element_count(DELong): 
        The element count for the next cross line.
         
    """ 
    if length_cross_line < ranges[0]:
        element_count = 5
    elif (length_cross_line >= ranges[0] and length_cross_line < ranges[1]):
        element_count = 5
        i = ranges[0]
        while i <= length_cross_line:
            i = i + ranges[2]
            element_count = element_count + 1  
    elif length_cross_line >= ranges[1]:
        element_count = 11      
    
    logger.debug(
        "returns the number of elements for the next row: "
        + str(element_count) + " elements."
        )   
        
    return element_count