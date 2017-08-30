"""
Created on 29.06.2017

@author: Matthias Hensen

Concatenate the functions of the python logging module and the arcpy 
messages mechanism. 

Therefore the method emit(self, record) is extended in a 
FileHandler-Subclass for creating arcpy messages with the same logging
level as the standard python logging module.

class ArcPyHandler(logging.handlers.FileHandler):
    Creates a modified FileHandler.

emit(self , record): 
    Extends the same-named function of FileHandler.

"""

import logging
from logging import FileHandler

import arcpy


class ArcPyHandler(FileHandler):
    """ Create a modified FileHandler - Class."""    
    def emit(self, record):
        """
        extend: Emit a record.

        Output the record to the file, catering for rollover as
        described in doRollover(). 
        
        If the levelno is 10 (DEBUG) or 20 (INFO), the record message
        (record.msg) is in use to create an arcpy message, if the
        levelno is 30 (WARNING), the record message is in use ti create
        an arcpy warning message and if the levelno is 40 (ERROR) or 50
        (CRITICAL), the record message is in use to create an arcpy
        error message 
        
        @param record(String): 
            Record is the message which will be logged.
        
        """
        try:
            logging.FileHandler.emit(self, record)
            if (record.levelno == 10 or record.levelno == 20):
                arcpy.AddMessage(record.msg)
            elif record.levelno == 30:
                arcpy.AddWarning(record.msg)
            elif (record.levelno == 40 or record.levelno == 50):
                arcpy.AddError(record.msg)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)