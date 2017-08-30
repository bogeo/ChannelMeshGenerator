"""
Created on 21.07.2017

@author: Matthias Hensen

Export the input features in different formats.

function: export_features_to_feature_class(
    in_features, out_path, out_name)
    
function: export_features_to_esri_shape(in_features, out_path, out_name)
    
function: export_features_to_ascii_xyz(
    in_features, out_path, out_name, fields),
    
function: export_features_to_autocad(
    in_features, out_path, out_name, autocad_type)
    
"""


import logging

import arcpy

from configuration.configure_logging import create_logger


logger = logging.getLogger(__name__)
create_logger(logger)


def export_features_to_feature_class(in_features, out_path, out_name):
    """Export the input features to a feature class.
    
    The feature class is created in a new file geodatabase.
    
    @param in_features(DEFeatureClass):
        The input features which are exported to a feature class.
    @param out_path(DEFolder):
        The output path.
    @param out_name(GPString):
        The name of the output file.        
            
    @return out_features(DEFeatureClass): 
        The output feature class
         
    """
    logger.debug("Start exporting features to feature class.")
    gdb_name = "feature_class"
    arcpy.CreateFileGDB_management(out_path, gdb_name)
    out_path = out_path + "/feature_class.gdb/"
    out_features = arcpy.FeatureClassToFeatureClass_conversion(
        in_features, out_path, out_name
        )
    logger.info("Exporting features to feature class finished successfully.")

    return out_features


def export_features_to_esri_shape(in_features, out_path, out_name):
    """Export the input features to an esri shapefile.
    
    After creating an output folder 'esri_shape' the function 
    FeatureClassToFeatureClass_conversion is executed. The output file 
    is a shapefile, because there is a normal file and not a file 
    geodatabase specified as output folder.
    
    @param in_features(DEFeatureClass):
        The input features which are exported to an esri shapefile.
    @param out_path(DEFolder):
        The output path.
    @param out_name(GPString):
        The name of the output file.        
            
    @return out_shape(DEShapefile): 
        The output shape file
         
    """
    logger.debug("Start exporting features to esri shape.")
    folder_name = "esri_shape"
    arcpy.CreateFolder_management(out_path, folder_name)
    out_path = out_path + "/" + folder_name
    out_shape = arcpy.FeatureClassToFeatureClass_conversion(
        in_features, out_path, out_name
        )
    logger.info("Exporting features to esri shape finished successfully.")

    return out_shape


def export_features_to_ascii_xyz(in_features, out_path, out_name, fields):
    """Export the input features to an ascii xyz file.
    
    Therefore an output folder 'ascii' is created. A temporary feature
    class is created to display the coordinates. Then the function 
    ExportXYv_stats is called and executed. Finally the temporary
    feature class is deleted.
    
    @param in_features(DEFeatureClass):
        The input features which are exported to an ascii xyz file.
    @param out_path(DEFolder):
        The output path.
    @param out_name(GPString):
        The name of the output file. 
    @param fields(GPString):
        The field names of the input file.       
            
    @return out_ascii(DEFile): 
        The output ascii xyz file
         
    """
    logger.debug(
        "Create feature class 'temp_features' and display coordinates."
        )
    temp_features = "temp_features"
    arcpy.CopyFeatures_management(in_features, temp_features)
    arcpy.AddXY_management(temp_features)
    logger.info(
        "Creating 'temp_features' and displaying coordinates finished "
        "successfully."
        )
    
    logger.debug("Start exporting features to ascii xyz.")
    folder_name = "ascii"
    arcpy.CreateFolder_management(out_path, folder_name)
    out_file = out_path + "/" + folder_name + "/" + out_name + ".xyz"
    try:
        fields = fields.split(";")
        value_fields = ["Point_Z", fields]
    except AttributeError:    
        value_fields = ["Point_Z"]
    delimiter = "SPACE"
    add_field_names_to_output = "ADD_FIELD_NAMES"
    out_ascii = arcpy.ExportXYv_stats(
        temp_features, value_fields, delimiter, out_file,
        add_field_names_to_output
        )
    logger.info("Exporting features to ascii xyz finished successfully.")
    
    logger.debug("Delete feature class 'temp_features'.")
    arcpy.Delete_management(temp_features)
    logger.debug("Feature class 'temp_features' deleted successfully.")

    return out_ascii

def export_features_to_autocad(
        in_features, out_path, out_name, autocad_type):
    """Export the input features to an autocad file.
    
    First, an output folder 'autocad' is created. Then the function
    ExportCAD_conversion is called and executed.
    
    @param in_features(DEFeatureClass):
        The input features which are exported to an autocad file.
    @param out_path(DEFolder):
        The output path.
    @param out_name(GPString):
        The name of the output file. 
    @param autocad type(GPString):
        The autocad file version.       
            
    @return out_autocad(DEFile): 
        The output autocad file
         
    """
    logger.debug("Start exporting features to autocad.")
    folder_name = "autocad"
    arcpy.CreateFolder_management(out_path, folder_name)
    if autocad_type == "DGN_V8": 
        out_file = out_path + "/" + folder_name + "/" + out_name + ".DGN"
    elif (autocad_type == "DWG_R14" or autocad_type == "DWG_R2000" 
            or autocad_type == "DWG_R2004" or autocad_type == "DWG_R2005" 
            or autocad_type == "DWG_R2007" or autocad_type == "DWG_R2010" 
            or autocad_type == "DWG_R2013"):
        out_file = out_path + "/" + folder_name + "/" + out_name + ".DWG"
    elif (autocad_type == "DXF_R14" or autocad_type == "DXF_R2000"
            or autocad_type == "DXF_R2004" or autocad_type == "DXF_R2005"
            or autocad_type == "DXF_R2007" or autocad_type == "DXF_R2010"
            or autocad_type == "DXF_R2013"):
        out_file = out_path + "/" + folder_name + "/" + out_name + ".DXF"
    out_autocad = arcpy.ExportCAD_conversion(
        in_features, autocad_type, out_file
        )
    logger.info("Exporting features to autocad finished successfully.")
    
    return out_autocad