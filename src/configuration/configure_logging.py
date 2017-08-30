"""
Created on 28.06.2017

@author: Matthias Hensen

Configure the logging settings.

function: create_logger(logger)

"""

import logging
import sys

from configuration.create_arcpy_log_file_handler import ArcPyHandler


def create_logger(logger):
    """Configure a logger object.
    
    First, the logging level is set. Then an 'ArcPyHandler' - object is 
    created to configure the filename, filemode and file encoding. After
    that a formatter is created to format the messages and the date. The
    formatter is added to the 'ArcPyHandler'.
    
    @param logger(Logger):
        The logger object which is configured.
    
    @return logger(Logger):
        The configured logger object.
        
    """
    level = logging.DEBUG 
    filename = sys.path[0] + "\logfile.log"
    filemode = "a"
    encoding = "utf-8"
    delay = False
    logger_format = (
        "%(name)s: %(asctime)s - %(lineno)s - %(levelname)s: %(message)s"
        )
    datefmt = "%d.%m.%Y %H:%M:%S"
    
    logger.setLevel(level)
    handler = ArcPyHandler(filename, filemode, encoding, delay)
    handler.setLevel(level)
    formatter = logging.Formatter(fmt = logger_format, datefmt = datefmt)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger