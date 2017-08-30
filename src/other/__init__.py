"""
Created on 04.07.2017

@author: Matthias Hensen

Package with useful modules and functions.

The functions are used often in all the other modules. The functions and
parameters are explained in the respective modules.

module convert_spatial_reference:
    Converts the input spatial reference name to a string which is used 
    as parameter item by the function arcpy.SpatialReference(item).
module list_field_names:
    List the field names of an input table.
module overwrite_output_settings:
    Set the env.overwriteOutput parameter.
module sort_features:
    Sort features and save these in a same-named feature class.

"""