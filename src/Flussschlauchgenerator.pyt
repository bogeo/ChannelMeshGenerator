"""
Created on 03.07.2017

@author: Matthias Hensen

This module defines the toolbox 'Flussschlauchgenerator.pyt'.

The class names are listed below. The parameters and detailed 
functionalities are explained in the classes themselves.

class Toolbox:
    Define the toolbox Flussschlauchgenerator.
class ConnectCrossSections:
    Tool that loads and connects cross sections to lines.
class CreateStreamCenterLine:
    Tool that creates the center line of a stream.
class AdjustInputData:
    Tool that adjusts the input data to the investigated area.
class CreateStreamPolygon:
    Tool that creates the investigated area as polygon.
class SubdivideWaterLandBorder:
    Tool that subdivides the water land border.
class CreateIntermediateCrossSections:
    Tool that creates intermediate cross sections 
class CreateLongitudinalSections:
    Tool that creates longitudinal sections.
class InterpolateLongitudinalSections
    Tool that interpolates the longitudinal sections height values.
class CreateDTMW:
    Tool that creates the digital terrain model of the watercourse.
class ExportFeatures:
    Tool that exports the input features in different formats.
class CreateTIN:
    Tool that creates a triangulated irregular network.
class CreateVertices:
    Tool that creates the vertices for the channel mesh.
class CreateChannelMeshElements:
    Tool that creates the elements for the channel mesh.
class CheckChannelMeshElements:
    Tool that checks the element area and angle sizes.
    
"""

import logging
import time

import arcpy

from configuration.configure_logging import create_logger

from dtmw.create_cross_lines import create_cross_lines
from dtmw.create_dtmw import create_dtmw
from dtmw.create_longitudinal_sections import create_longitudinal_sections
from dtmw.interpolate_longitudinal_sections import (
    interpolate_longitudinal_sections)

from export.create_tin import create_tin
from export.export_features import (
    export_features_to_ascii_xyz, export_features_to_autocad,
    export_features_to_esri_shape, export_features_to_feature_class)

from mesh.check_channel_mesh_elements import check_channel_mesh_elements
from mesh.create_channel_mesh_elements import create_channel_mesh_elements
from mesh.create_vertices import create_vertices

from other.convert_spatial_reference import convert_spatial_reference
from other.list_field_names import list_field_names
from other.overwrite_output_settings import overwrite_output_settings
from other.sort_features import sort_features

from preparation.bound_features_to_investigated_area import (
    bound_features_to_investigated_area, create_bounding_features,
    create_cutting_features)
from preparation.connect_cross_sections import (
    check_duplicated_cross_sections, connect_cross_sections_with_indication, 
    connect_cross_sections_without_indication
    )
from preparation.create_stream_center_line import create_stream_center_line
from preparation.create_stream_polygon import create_stream_polygon
from preparation.flip_line import (flip_line_direction, flip_line_numeration)
from preparation.load_points import (
    load_points, load_points_from_multiple_files)
from preparation.subdivide_water_land_border import subdivide_water_land_border


logger = logging.getLogger("Flussschlauchgenerator.pyt")
create_logger(logger)


class Toolbox(object):
    """Define the toolbox 'Flussschlauchgenerator.pyt'.
    
    The toolbox has four toolsets: 'Berechnungsnetz',
    'Datenaufbereitung', 'DGM-W' and 'Export'. 'Berechnungsnetz'
    contains the tools 'CreateVertices', 'CreateChannelMeshElements' and
    'CheckChannelMeshElements'. 'Datenaufbereitung' contains the tools
    'ConnectCrossSections', 'CreateStreamCenterLine', 'AdjustInputData',
    'CreateStreamPolygon' and 'SubdivideWaterLandBorder'. 'DGM-W'
    contains the tools 'CreateIntermediateCrossSections',
    'CreateLongitudinalSections', 'InterpolateLongitudinalSections' and
    'CreateDTMW'. 'Export' contains the tools 'ExportFeatures' and
    'CreateTIN'. The tool parameters and functionality are listed below 
    in the tool classes.
    
    """
    def __init__(self):
        """Define the toolbox 'Flussschlauchgenerator'.
        
        The tools are added in the self.tools method.
        
        """
        self.label = "Flussschlauchgenerator"
        self.alias = "cmg"
        self.tools = [
            ConnectCrossSections, CreateStreamCenterLine, AdjustInputData,
            CreateStreamPolygon, SubdivideWaterLandBorder,
            CreateIntermediateCrossSections, CreateLongitudinalSections,
            InterpolateLongitudinalSections, CreateDTMW, ExportFeatures, 
            CreateTIN, CreateVertices, CreateChannelMeshElements,
            CheckChannelMeshElements
            ]


class ConnectCrossSections(object):
    """Tool that loads and connects cross sections to lines.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'ConnectCrossSections'."""
        self.label = "Verbinde Querprofile"
        self.description = (
            "Verbindet die punktuell gemessenen Querprofile zu Linien. "
            "Eingangsformate der Punkte k\xf6nnen ASCII - Dateien (txt oder "
            "xyz) sowie csv - Dateien sein. Wenn ein Verbinungsfeld (zum "
            "Beispiel eine Kilometerangabe) mit den Punkten verkn\xfcpft ist, "
            "werden die Punkte, deren Feldwert identisch ist, miteinander "
            "verbunden. Ist keine Angabe vorhanden, werden die Abst\xe4nde "
            "zwischen den einzelnen Punkten berechnet und jeweils die beiden "
            "n\xe4chsten Punkte verbunden, solange der Abstand kleiner als "
            "eine vorher festgelegte Entfernung (standardm\xe4\xdfig 10 "
            "Meter) ist. Anschlie\xdfend wird noch gepr\xfcft, ob Querprofile "
            "doppelt vorhanden sind."
            )
        self.canRunInBackground = True
        self.category = "Datenaufbereitung"

    def getParameterInfo(self):
        """Define parameter definitions for 'ConnectCrossSections'.
        
        @param param0 in_cross_sections(DEFeatureClass):
            The input cross section points feature class. The parameter
            is filtered to 'Point'.
        @param param1 load_point_file(GPBoolean):
            Load points from file?
        @param param2 workspace(DEWorkspace):
            Workspace for results. The parameter is filtered to 'Local
            Database'.
        @param param3 in_points(DEFile):
            File which contains the cross sections. The parameter is
            filtered to 'txt', 'csv' and 'xyz'.
        @param param4 out_cross_section_points_name(GPString): 
            Name of the feature class with the cross section points.
        @param param5 out_cross_section_lines_name(GPString):
            Name of the feature class with the cross section lines.
        @param param6 spatial_reference(GPSpatialReference):
            Spatial reference system, e.g. as epsg-code. The default
            value is '25832' (epsg-code).
        @param param7 indication(GPBoolean): 
            Indication available? The default value is 'True'.
        @param param8 maximum_distance(GPDouble): 
            The maximum distance between successive points. The default
            value is '10.0' meters. The parameter range is filtered from
            '1.0' meters to '50.0' meters.
        @param param9 line_field(GPString):
            The line field for the connection.
        @param param10 in_x_field(GPString):
            The input x field.
        @param param11 in_y_field(GPString):
            The input y field.
        @param param12 in_z_field(GPString):
            The input z field.
        @param param13 decimal_separator(GPString):
            The decimal separator. The default value is 'DECIMAL_POINT'.
            The parameter is filtered to 'DECIMAL_POINT' and
            'DECIMAL_COMMA'.
        @param param14 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
        
        """ 
        param0 = arcpy.Parameter(
            displayName=(
                "Querprofile Punkte Feature Class (In cross section points)"
                ),
            name="in_cross_sections",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input"
            )
        param0.filter.list = ["Point"]
        
        param1 = arcpy.Parameter(
            displayName="Punkte einladen? (Load points?)",
            name="load_point_file",
            datatype="GPBoolean",
            parameterType="Required",
            direction="Input"
            )
        param1.value = True
        
        param2 = arcpy.Parameter(
            displayName="Ausgabe-Geodatabase (Workspace)",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
            )
        param2.filter.list = ["Local Database"]
            
        param3 = arcpy.Parameter(
            displayName="Querprofile Punktdatei (In cross section point file)",
            name="in_points",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input"
            )
        param3.filter.list = ["txt", "csv", "xyz"]
                    
        param4 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der Punkte (Out cross "
                "section points name)"
                ),
            name="out_cross_section_points_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
         
        param5 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der verbundenen Querprofile "
                "(Out cross section lines name)"
                ),
            name="out_cross_section_lines_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param6 = arcpy.Parameter(
            displayName="SpatialReference (EPSG)",
            name="spatial_reference",
            datatype="GPSpatialReference",
            parameterType="Optional",
            direction="Input"
            )
        param6.value = 25832
         
        param7 = arcpy.Parameter(
            displayName="Verbindungsfeld vorhanden? (Indication available?)",
            name="indication",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param7.value = True
        
        param8 = arcpy.Parameter(
            displayName=(
                "Maximale Distanz zwischen zwei Punkten [m]? (Maximum "
                "distance between successive points[m]?)"
                ),
            name="maximum_distance",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input"
            )
        param8.value = "10.0"
        param8.filter.type = "Range"
        param8.filter.list = [1.0, 50.0]
        
        param9 = arcpy.Parameter(
            displayName="Linienfeld (Line field)",
            name="line_field",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param10 = arcpy.Parameter(
            displayName="X-Feld (In x field)",
            name="in_x_field",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param11 = arcpy.Parameter(
            displayName="Y-Feld (In y field)",
            name="in_y_field",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )

        param12 = arcpy.Parameter(
            displayName="Z-Feld (In z field)",
            name="in_z_field",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param13 = arcpy.Parameter(
            displayName="Dezimaltrennzeichen (Decimal separator xyz files)",
            name="decimal_separator",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        param13.value = "DECIMAL_POINT"
        param13.filter.type = "ValueList"
        param13.filter.list = ["DECIMAL_POINT", "DECIMAL_COMMA"]
        
        param14 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param14.value = True
         
        params = [
            param0, param1, param2, param3, param4, param5, param6, param7,
            param8, param9, param10, param11, param12, param13, param14
            ]
        
        return params

    def isLicensed(self):
        """Allow the tool to execute, only if the extension 'ArcGIS 3D
        Analyst' is available.
        
        """
        try:
            if arcpy.CheckExtension("3D") != "Available":
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("Extension '3D Analyst' is unavailable.")
            return False

        return True

    def updateParameters(self, parameters):
        """Modify the values, properties and display of parameters.
        
        This method is called whenever a parameter has been changed.
        
        """ 
        if parameters[1].value:
            parameters[3].enabled = True
            parameters[4].enabled = True
            parameters[6].enabled = True
            parameters[9].enabled = True
            parameters[0].enabled = False
            if parameters[3].value:
                desc = arcpy.Describe(parameters[3].valueAsText)
                if (desc.extension == "csv" or desc.extension == "txt"):
                    parameters[7].enabled = True
                    parameters[9].enabled = True
                    parameters[10].enabled = True
                    parameters[11].enabled = True
                    parameters[12].enabled = True
                    parameters[13].enabled = False
                elif desc.extension == "xyz":
                    parameters[7].enabled = False
                    parameters[7].value = False
                    parameters[9].enabled = False
                    parameters[10].enabled = False
                    parameters[11].enabled = False
                    parameters[12].enabled = False
                    parameters[13].enabled = True
        else:
            parameters[3].enabled = False
            parameters[4].enabled = False
            parameters[6].enabled = False
            parameters[10].enabled = False
            parameters[11].enabled = False
            parameters[12].enabled = False
            parameters[13].enabled = False
            parameters[0].enabled = True
        
        if parameters[7].value:
            parameters[9].enabled = True
            parameters[8].enabled = False
        else:
            parameters[9].enabled = False
            parameters[8].enabled = True
        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal parameter validation.
        
        This method is called after internal validation.
        
        """
        if (not parameters[1].value and not parameters[0].value):
            parameters[0].setErrorMessage("Eingabewert erforderlich.")
        elif parameters[1].value:
            if not parameters[3].value:
                parameters[3].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[4].value:
                parameters[4].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[6].value:
                parameters[6].setErrorMessage("Eingabewert erforderlich.")
            if parameters[3].value:
                desc = arcpy.Describe(parameters[3].valueAsText)
                if (desc.extension == "csv" or desc.extension == "txt"):
                    if not parameters[10].value:
                        parameters[10].setErrorMessage(
                            "Eingabewert erforderlich."
                            )                    
                    if not parameters[11].value:
                        parameters[11].setErrorMessage(
                            "Eingabewert erforderlich."
                            )
                    if not parameters[12].value:
                        parameters[12].setErrorMessage(
                            "Eingabewert erforderlich."
                            )
                elif desc.extension == "xyz":
                    if not parameters[13].value:
                        parameters[13].setErrorMessage(
                            "Eingabewert erforderlich."
                            )
        
        if (parameters[7].value and not parameters[9].value):
            parameters[9].setErrorMessage("Eingabewert erforderlich.")
        elif (not parameters[7].value and not parameters[8].value):
            parameters[8].setErrorMessage("Eingabewert erforderlich.")
            
        if (parameters[8].value and parameters[8].hasError()):
            parameters[8].setErrorMessage(
                "Zul\xe4ssiger Wertebereich liegt zwischen 1,0 - 50,0. "
                "Als Dezimaltrennzeichen bitte ',' verwenden."
                )
          
        if (parameters[13].value and parameters[13].hasError()):
            parameters[13].setErrorMessage(
                "Zul\xe4ssige Werte: 'DECIMAL_POINT', 'DECIMAL_COMMA'."
                )
        
        return

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. If load points
        is 'True', the parameter spatial_reference is converted to 
        string and the cross section points are loaded from the input 
        file to a point feature class. This feature class is the input 
        for the connection. Which function is called for the connection
        is depending on whether a line field is available. After the 
        connection duplicated cross sections are checked and - if 
        existing - one of them is deleted.
        
        """
        in_cross_sections = parameters[0].valueAsText
        load_point_file = parameters[1].value
        workspace = parameters[2].valueAsText
        in_points = parameters[3].valueAsText
        out_cross_section_points_name = parameters[4].valueAsText
        out_cross_section_lines_name = parameters[5].valueAsText
        spatial_reference = parameters[6].valueAsText
        indication = parameters[7].value
        maximum_distance = parameters[8].value
        line_field = parameters[9].valueAsText
        in_x_field = parameters[10].valueAsText
        in_y_field = parameters[11].valueAsText
        in_z_field = parameters[12].valueAsText
        decimal_separator = parameters[13].valueAsText
        overwrite_output = parameters[14].value
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        if load_point_file:
            logger.info("Start function convert_spatial_reference.")
            spatial_reference = convert_spatial_reference(spatial_reference)
            logger.info("Convert_spatial_reference finished successfully.")
        
            logger.info("Start function load_points.")
            in_cross_sections = load_points(
                workspace, in_points, out_cross_section_points_name,
                spatial_reference, in_x_field, in_y_field, in_z_field,
                decimal_separator
                )
            logger.info("Load_points finished successfully.")
        
        logger.info("Check if indication is available.")
        if indication:
            logger.info(
                "Indication available. Start function "
                "connect_cross_sections_with_indication."
                )
            in_cross_sections = connect_cross_sections_with_indication(
                workspace, in_cross_sections, out_cross_section_lines_name,
                line_field, maximum_distance
                )
            logger.info(
                "Connect_cross_sections_with_indication finished successfully."
                )
        else:
            logger.info(
                "Indication not available. Start function "
                "connect_cross_sections_without_indication."
                )
            in_cross_sections = connect_cross_sections_without_indication(
                workspace, in_cross_sections, out_cross_section_lines_name,
                maximum_distance
                )
            logger.info(
                "Connect_cross_sections_without_indication finished "
                "successfully."
                )

        logger.info("Start function check_duplicated_cross_sections.")
        check_duplicated_cross_sections(in_cross_sections)
        logger.info("Check_duplicated_cross_sections finished successfully.")
        
        return


class CreateStreamCenterLine(object):
    """Tool that creates the center line of a stream.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'CreateStreamCenterLine'."""
        self.label = "Erstelle Gew\xe4sserachse"
        self.description = (
            "Erstellt die Gew\xe4sserachse, indem die mittlere Linie zwischen "
            "den beiden WLG (Uferlinien) extrahiert wird."
            )
        self.canRunInBackground = True
        self.category = "Datenaufbereitung"

    def getParameterInfo(self):
        """Define parameter definitions for 'CreateStreamCenterLine'.
        
        @param param0 workspace(DEWorkspace):
            Workspace for results. The parameter is filtered to 'Local
            Database'.
        @param param1 in_wlb(DEFeatureClass):
            The input water land border feature class. The parameter is
            filtered to 'Polyline'.
        @param param2 out_stream_center_line_name(GPString): 
            The name of the feature class with the stream center line.
        @param param3 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
        
        """ 
        param0 = arcpy.Parameter(
            displayName="Ausgabe-Geodatabase (Workspace)",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
            )
        param0.filter.list = ["Local Database"]
            
        param1 = arcpy.Parameter(
            displayName="WLG /Uferlinien (In water land border)",
            name="in_wlb",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param1.filter.list = ["Polyline"]    
            
        param2 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der Gew\xe4sserachse (Out "
                "stream center line name.)"
                ),
            name="out_stream_center_line_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param3 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param3.value = True
         
        params = [param0, param1, param2, param3]
        
        return params

    def isLicensed(self):
        """Allow the tool to execute, only if the 'ArcGIS for Desktop
        Advanced' license is available.
        
        """
        try:
            if (arcpy.CheckProduct("arcinfo") != "AlreadyInitialized"
                    and arcpy.CheckProduct("arcinfo") != "Available"):
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("ArcGIS for Desktop Advanced license is unavailable.")
            return False

        return True

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. Then the 
        function create_stream_center_line is called and executed.
        
        """
        workspace = parameters[0].valueAsText
        in_wlb = parameters[1].valueAsText
        out_stream_center_line_name = parameters[2].valueAsText
        overwrite_output = parameters[3].value
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        logger.info("Start function create_stream_center_line.")
        create_stream_center_line(
            workspace, in_wlb, out_stream_center_line_name
            )
        logger.info("Create_stream_center_line finished successfully.")

        return


class AdjustInputData(object):
    """Tool that adjusts the input data to the investigated area.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'AdjustInputData'."""
        self.label = "Passe Eingangsdaten an"
        self.description =  (
            "Dieses Werkzeug stellt mehrere Funktionen bereit, mit denen die "
            "Eingangsdaten angepasst werden k\xf6nnen. Dazu geh\xf6ren das "
            "Zurechtschneiden von Querprofilen, WLG und Gew\xe4sserachse auf "
            "den Untersuchungsbereich, die \xfcberpr\xfcfung und das Drehen "
            "der Richtung der WLG und der Querprofile sowie die Umkehrung der "
            "Nummerierung der Querprofile." 
            )
        self.canRunInBackground = True
        self.category = "Datenaufbereitung"

    def getParameterInfo(self):
        """Define parameter definitions for 'AdjustInputData'.
        
        @param param0 bound_cross_sections(GPBoolean): 
            Bound_cross_sections? The default value is 'True'.
        @param param1 bound_wlb(GPBoolean): 
            Bound_wlb? The default value is 'True'.
        @param param2 bound_stream_center_line(GPBoolean): 
            Bound_stream_center_line? The default value is 'True'.
        @param param3 flip_cross_sections(GPBoolean): 
            Flip_cross_sections? The default value is 'True'.
        @param param4 flip_wlb(GPBoolean): 
            Flip_wlb? The default value is 'True'.
        @param param5 flip_numeration(GPBoolean):
            Flip_numeration? The default value is 'False'.
        @param param6 in_cross_sections(DEFeatureClass):
            The input cross sections feature class. The parameter is
            filtered to 'Polyline'.
        @param param7 in_wlb(DEFeatureClass):
            The input water land border feature class. The parameter is
            filtered to 'Polyline'.
        @param param8 in_stream_center_line(DEFeatureClass):
            The input stream center line feature class. The parameter is 
            filtered to 'Polyline'.
        @param param9 keep_names(GPBoolean):
            Keep_names? The default value is 'True'.
        @param param10 workspace(DEWorkspace):
            Workspace for results. The parameter is filtered to 'Local
            Database'.
        @param param11 out_cross_sections_name(GPString): 
            The name of the feature class with the adjusted cross
            sections.
        @param param12 out_wlb_name(GPString):
            The name of the feature class with the adjusted water land 
            border.
        @param param13 out_stream_center_line_name(GPString):
            The name of the feature class with the adjusted stream 
            center line.
        @param param14 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
        
        """ 
        param0 = arcpy.Parameter(
            displayName=(
                "Begrenze Querprofile auf Untersuchungsbereich (Bound cross "
                "sections)"
                ),
            name="bound_cross_sections",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param0.value = True 
        
        param1 = arcpy.Parameter(
            displayName=(
                "Begrenze WLG / Uferlinien auf Untersuchungsbereich (Bound "
                "water land border)"
                ),
            name="bound_wlb",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param1.value = True  
        
        param2 = arcpy.Parameter(
            displayName=(
                "Begrenze Gew\xe4sserachse auf Untersuchungsbereich (Bound "
                "stream center line)"
                ),
            name="bound_stream_center_line",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param2.value = True 

        param3 = arcpy.Parameter(
            displayName=(
                "Pr\xfcfe und korrigiere Richtung der Querprofile (Flip "
                "cross sections direction)"
                ),
            name="flip_cross_sections",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param3.value = True 
        
        param4 = arcpy.Parameter(
            displayName=(
                "Pr\xfcfe und korrigiere Richtung der WLG /Uferlinien (Flip "
                "water land borders direction)"
                ),
            name="flip_wlb",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param4.value = True 
        
        param5 = arcpy.Parameter(
            displayName=(
                "Kehre Nummerierung der Querprofile um (Flip cross sections "
                "numeration)"
                ),
            name="flip_numeration",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param5.value = False
            
        param6 = arcpy.Parameter(
            displayName="Querprofile (In cross sections)",
            name="in_cross_sections",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param6.filter.list = ["Polyline"]
        
        param7 = arcpy.Parameter(
            displayName="WLG /Uferlinien (In water land border)",
            name="in_wlb",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input"
            )
        param7.filter.list = ["Polyline"]
        
        param8 = arcpy.Parameter(
            displayName="Gew\xe4sserachse (In stream center line)",
            name="in_stream_center_line",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input"
            )
        param8.filter.list = ["Polyline"]
        
        param9 = arcpy.Parameter(
            displayName=(
                "Namen behalten: Ausgangsdaten = Eingangsdaten? (keep names: "
                "output names = input names?)"
                ),
            name="keep_names",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param9.value = True 
        
        param10 = arcpy.Parameter(
            displayName="Ausgabe-Geodatabase (Workspace)",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input"
            )
        param10.filter.list = ["Local Database"]
        
        param11 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der Querprofile (Out cross "
                "sections name)"
                ),
            name="out_cross_sections_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param12 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der WLG/Uferlinien (Out water "
                "land border name)"
                ),
            name="out_wlb_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
            
        param13 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der Gew\xe4sserachse (Out "
                "stream center line name)"
            ),
            name="out_stream_center_line_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param14 = arcpy.Parameter(
            displayName="Vorhandene Daten \xfcberschreiben?",
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param14.value = True
         
        params = [
            param0, param1, param2, param3, param4, param5, param6, param7,
            param8, param9, param10, param11, param12, param13, param14
            ]
        
        return params

    def isLicensed(self):
        """Allow the tool to execute, only if the 'ArcGIS for Desktop
        Advanced' license is available.
        
        """
        try:
            if (arcpy.CheckProduct("arcinfo") != "AlreadyInitialized"
                    and arcpy.CheckProduct("arcinfo") != "Available"):
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("ArcGIS for Desktop Advanced license is unavailable.")
            return False

        return True
    
    def updateParameters(self, parameters):
        """Modify the values, properties and display of parameters.
        
        This method is called whenever a parameter has been changed.
        
        """
        if parameters[9].value:
            parameters[10].enabled = False
            parameters[11].enabled = False
            parameters[12].enabled = False
            parameters[13].enabled = False
            parameters[14].enabled = False
            parameters[14].value = True
        else:
            parameters[10].enabled = True
            if (parameters[0].value or parameters[3].value
                    or parameters[5].value):
                parameters[11].enabled = True
            else:
                parameters[11].enabled = False
            if (parameters[1].value or parameters[4].value):
                parameters[12].enabled = True
            else:
                parameters[12].enabled = False
            if parameters[2].value:
                parameters[13].enabled = True
            else:
                parameters[13].enabled = False
            parameters[14].enabled = True
        
        if parameters[3].value:
            parameters[0].value = True
            parameters[0].enabled = False
        else:
            parameters[0].enabled = True
            
        if parameters[4].value:
            parameters[0].value = True
            parameters[1].value = True
            parameters[0].enabled = False
            parameters[1].enabled = False
        else:
            parameters[1].enabled = True
            if not parameters[3].value:
                parameters[0].enabled = True
            
        if (parameters[5].value and not parameters[0].value
                and not parameters[1].value and not parameters[2].value
                and not parameters[3].value and not parameters[4].value):
            parameters[7].enabled = False
            parameters[8].enabled = False
        else:
            parameters[7].enabled = True
            parameters[8].enabled = True

        return
    
    def updateMessages(self, parameters):
        """Modify the messages created by internal parameter validation.
        
        This method is called after internal validation.
        
        """
        if (not parameters[0].value and not parameters[1].value
                and not parameters[2].value and not parameters[3].value
                and not parameters[4].value and not parameters[5].value):
            parameters[0].setErrorMessage("Keine Aufgabe ausgew\xe4hlt.")
            parameters[1].setErrorMessage("Keine Aufgabe ausgew\xe4hlt.")
            parameters[2].setErrorMessage("Keine Aufgabe ausgew\xe4hlt.")
            parameters[3].setErrorMessage("Keine Aufgabe ausgew\xe4hlt.")
            parameters[4].setErrorMessage("Keine Aufgabe ausgew\xe4hlt.")
            parameters[5].setErrorMessage("Keine Aufgabe ausgew\xe4hlt.")
        
        if not parameters[9].value:
            if not parameters[10].value:
                parameters[10].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[11].value:
                if (parameters[0].value or parameters[3].value
                        or parameters[5].value):
                    parameters[11].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[12].value:
                if (parameters[1].value or parameters[4].value):
                    parameters[12].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[13].value:
                if parameters[2].value:
                    parameters[13].setErrorMessage("Eingabewert erforderlich.")
            
        
        if not parameters[7].value:
            if (parameters[0].value or parameters[1].value
                    or parameters[3].value or parameters[4].value):
                parameters[7].setErrorMessage("Eingabewert erforderlich.")
        
        if not parameters[8].value:
            if (parameters[0].value or parameters[2].value):
                parameters[8].setErrorMessage("Eingabewert erforderlich.")    
            
        return

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. Depending on
        which tasks are selected, the individual functions are called
        and executed. If bound_cross_sections is selected, the cross
        sections are bounded to the investigated area. If
        flip_cross_sections is selected, the cross sections are checked
        and flipped if necessary. If bound_wlb or 
        bound_stream_center_line are selected, the bounding features and 
        cutting features are created in their same-named functions. If 
        bound_wlb is selected, the water land border is bounded to the 
        investigated area and if bound_stream_center_line is selected, 
        the stream center line is bounded in the same way. After that, 
        the cutting and bounding features are deleted.  In the same way 
        as the cross sections, the water land border is checked and 
        flipped, if flip_wlb is selected. If flip_numeration is 
        selected, the SECTIONID if the cross sections is flipped.
        
        """
        bound_cross_sections = parameters[0].value
        bound_wlb = parameters[1].value
        bound_stream_center_line = parameters[2].value
        flip_cross_sections = parameters[3].value
        flip_wlb = parameters[4].value
        flip_numeration = parameters[5].value
        in_cross_sections = parameters[6].valueAsText
        in_wlb = parameters[7].valueAsText
        in_stream_center_line = parameters[8].valueAsText
        keep_names = parameters[9].value
        if not parameters[10].value:
            desc = arcpy.Describe(in_cross_sections)
            workspace = desc.path
        else:
            workspace = parameters[10].valueAsText
        out_cross_sections_name = parameters[11].valueAsText
        out_wlb_name = parameters[12].valueAsText
        out_stream_center_line_name = parameters[13].valueAsText
        overwrite_output = parameters[14].value
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        if bound_cross_sections:
            logger.info(
                "Start function bound_features_to_investigated_area to bound "
                "cross sections."
                )
            in_cross_sections = bound_features_to_investigated_area(
                workspace, in_cross_sections, in_wlb, [in_stream_center_line],
                out_cross_sections_name, keep_names
                )
            logger.info("Cross sections bounded successfully.")
            
            logger.debug("Sort adjusting features.")
            sort_fields = [["SECTIONID", "ASCENDING"]]
            sort_features(in_cross_sections, sort_fields)
            logger.info("Sorting adjusting features finished successfully.")
        
        if flip_cross_sections:
            logger.info(
                "Start function flip_line_direction to check and correct "
                "cross sections."
                )
            field_names = list_field_names(in_wlb)
            if "WLBID" in field_names:
                reference_where_clause = "WLBID = 1"
            else:
                reference_where_clause = "OBJECTID = 1"
            in_cross_sections = flip_line_direction(
                workspace, in_cross_sections, in_wlb, out_cross_sections_name,
                keep_names, reference_where_clause
                )
            logger.info("Cross sections checked and flipped successfully.")
            
        if (bound_wlb or bound_stream_center_line):
            logger.info("Start function create_bounding_features.")
            bounding_features = create_bounding_features(in_cross_sections)
            logger.info("Create_bounding_features finished successfully.")
            
            logger.info("Start function create_cutting_features.")
            cutting_features = create_cutting_features(in_cross_sections)
            logger.info("Create_cutting_features finished successfully.")
            
            if bound_wlb:
                logger.info(
                    "Start function bound_features_to_investigated_area to "
                    "bound water land border."
                    )
                in_wlb = bound_features_to_investigated_area(
                    workspace, in_wlb, bounding_features, cutting_features,
                    out_wlb_name, keep_names
                    )
                logger.info("Water land border bounded successfully.")
            
            if bound_stream_center_line:
                logger.info(
                    "Start function bound_features_to_investigated_area to "
                    "bound stream center line."
                    )
                bound_features_to_investigated_area(
                    workspace, in_stream_center_line, bounding_features,
                    cutting_features, out_stream_center_line_name, keep_names
                    )
                logger.info("Stream center line bounded successfully.")
            
            logger.info("Delete 'bounding_features'.")
            arcpy.Delete_management(bounding_features)
            logger.info("'bounding_features' deleted successfully.")
            
            logger.info("Delete cutting_features.")
            for cutting_feature in cutting_features:
                arcpy.Delete_management(cutting_feature)
            logger.info("Cutting_features deleted successfully.")
            
        if flip_wlb:
            logger.info(
                "Start function flip_line_direction to check and correct "
                "the water land border."
                )
            reference_where_clause = "OBJECTID = 1"
            flip_line_direction(
                workspace, in_wlb, in_cross_sections, out_wlb_name, keep_names,
                reference_where_clause
                )
            logger.info("Water land border checked and flipped successfully.")
            
        if flip_numeration:
            logger.info(
                "Start function flip_numeration to flip the cross section "
                "numeration."
                )
            flip_line_numeration(
                workspace, in_cross_sections, out_cross_sections_name,
                keep_names
                )
            logger.info("Cross section numeration flipped successfully.")

        return


class CreateStreamPolygon(object):
    """Tool that creates the investigated area as polygon.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'CreateStreamPolygon'."""
        self.label = "Erstelle Gew\xe4sserpolygon"
        self.description = (
            "Erstellt ein Gew\xe4sserpolygon des Untersuchungsgebiets, mit "
            "den \xe4u\xdferen Querprofilen und den WLG als Grenzen."
            )
        self.canRunInBackground = True
        self.category = "Datenaufbereitung"

    def getParameterInfo(self):
        """Define parameter definitions for 'CreateStreamPolygon'.
        
        @param param0 workspace(DEWorkspace):
            Workspace for results. The parameter is filtered to 'Local
            Database'.
        @param param1 in_cross_sections(DEFeatureClass):
            The input cross sections feature class. The parameter is
            filtered to 'Polyline'.
        @param param2 in_wlb(DEFeatureClass):
            The input water land border feature class. The parameter is 
            filtered to 'Polyline'.
        @param param3 out_stream_polygon_name(GPString): 
            The name of the feature class with the stream polygon.
        @param param4 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
        
        """ 
        param0 = arcpy.Parameter(
            displayName="Ausgabe-Geodatabase (Workspace)",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
            )
        param0.filter.list = ["Local Database"]
            
        param1 = arcpy.Parameter(
            displayName="Querprofile (In cross sections)",
            name="in_cross_sections",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param1.filter.list = ["Polyline"]
        
        param2 = arcpy.Parameter(
            displayName="WLG /Uferlinien (In water land border)",
            name="in_wlb",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param2.filter.list = ["Polyline"]
            
        param3 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der Gew\xe4sserpolygon ( Out "
                "stream polygon name)"
                ),
            name="out_stream_polygon_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param4 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param4.value = True
         
        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        """Allow the tool to execute, only if the 'ArcGIS for Desktop
        Advanced' license is available.
        
        """
        try:
            if (arcpy.CheckProduct("arcinfo") != "AlreadyInitialized"
                    and arcpy.CheckProduct("arcinfo") != "Available"):
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("ArcGIS for Desktop Advanced license is unavailable.")
            return False

        return True

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. The bounding 
        features (the outer cross sections) are created in the function
        create_bounding_features. Then the function 
        create_stream_polygon is called and executed.
        
        """
        workspace = parameters[0].valueAsText
        in_cross_sections = parameters[1].valueAsText
        in_wlb = parameters[2].valueAsText
        out_stream_polygon_name = parameters[3].valueAsText
        overwrite_output = parameters[4].value
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        logger.info("Start function create_bounding_features.")
        bounding_features = create_bounding_features(in_cross_sections)
        logger.info("Create_bounding_features finished successfully.")
        
        logger.info("Start function create_stream_polygon.")
        create_stream_polygon(
            workspace, bounding_features, in_wlb, out_stream_polygon_name
            )
        logger.info("Create_stream_polygon finished successfully.")

        return


class SubdivideWaterLandBorder(object):
    """Tool that subdivides the water land border.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'SubdivideWaterLandBorder'."""
        self.label = "Unterteile WLG (Uferlinien) in Abschnitte"
        self.description = (
            "Unterteilt die WLG (Uferlinien) an den Schnittpunkten mit den "
            "Querprofilen und f\xfcgt ihnen die zum Abschnitt passende ID "
            "hinzu."
            )
        self.canRunInBackground = True
        self.category = "Datenaufbereitung"

    def getParameterInfo(self):
        """Define parameter definitions for 'SubdivideWaterLandBorder'.
        
        @param param0 in_wlb(DEFeatureClass):
            The input water land border feature class. The parameter is
            filtered to 'Polyline'.
        @param param1 in_cross_sections(DEFeatureClass):
            The input cross section feature class. The parameter is 
            filtered to 'Polyline'.
        @param param2 keep_names(GPBoolean):
            Keep_names? The default value is 'True'.
        @param param3 workspace(DEWorkspace):
            Workspace for results. The parameter is filtered to 'Local
            Database'. 
        @param param4 out_wlg_subdivided_name(GPString): 
            The name of the feature class with the divided water land
            border
        @param param5 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
         
        """ 
        param0 = arcpy.Parameter(
            displayName="WLG /Uferlinien (In water land border)",
            name="in_wlb",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param0.filter.list = ["Polyline"]
        
        param1 = arcpy.Parameter(
            displayName="Querprofile (In cross sections)",
            name="in_cross_sections",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param1.filter.list = ["Polyline"]
        
        param2 = arcpy.Parameter(
            displayName=(
                "Namen behalten: Ausgangsdaten = Eingangsdaten? (keep names: "
                "output names = input names?)"
                ),
            name="keep_names",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param2.value = True 
        
        param3 = arcpy.Parameter(
            displayName="Ausgabe-Geodatabase (Workspace)",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input"
            )
        param3.filter.list = ["Local Database"]
        
        param4 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der unterteilten WLG (Out "
                "subdivided water land border name"
                ),
            name="out_wlg_subdivided_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param5 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param5.value = True
         
        params = [param0, param1, param2, param3, param4, param5]
        
        return params

    def isLicensed(self):
        """Allow the tool to execute, only if the 'ArcGIS for Desktop
        Advanced' license is available.
        
        """
        try:
            if (arcpy.CheckProduct("arcinfo") != "AlreadyInitialized"
                    and arcpy.CheckProduct("arcinfo") != "Available"):
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("ArcGIS for Desktop Advanced license is unavailable.")
            return False

        return True
    
    def updateParameters(self, parameters):
        """Modify the values, properties and display of parameters.
        
        This method is called whenever a parameter has been changed.
        
        """
        if parameters[2].value:
            parameters[3].enabled = False
            parameters[4].enabled = False
            parameters[5].enabled = False
            parameters[5].value = True
        else:
            parameters[3].enabled = True
            parameters[4].enabled = True
            parameters[5].enabled = True

        return
    
    def updateMessages(self, parameters):
        """Modify the messages created by internal parameter validation.
        
        This method is called after internal validation.
        
        """
        if not parameters[2].value:
            if not parameters[3].value:
                parameters[3].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[4].value:
                parameters[4].setErrorMessage("Eingabewert erforderlich.")
        
        return

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. Then the 
        function subdivide_water_land_border is called and executed.
        
        """
        in_wlb = parameters[0].valueAsText
        in_cross_sections = parameters[1].valueAsText
        keep_names = parameters[2].value
        workspace = parameters[3].valueAsText
        out_wlb_subdivided_name = parameters[4].valueAsText
        overwrite_output = parameters[5].value
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        logger.info("Start function subdivide_water_land_border.")
        subdivide_water_land_border(
            workspace, in_wlb, in_cross_sections, out_wlb_subdivided_name,
            keep_names
            )
        logger.info("Subdivide_water_land_border finished successfully.")

        return

    
class CreateIntermediateCrossSections(object):
    """Tool that creates intermediate cross sections.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'CreateIntermediateCrossSections'."""
        self.label = "Erstelle Zwischenprofile"
        self.description = (
            "Erstellt in einem festgelegten Abstand (standardm\xe4\xdfig 10 "
            "Meter) Zwischenprofile zwischen den einzelnen Querprofilen. Um "
            "Kurven besser zu ber\xfccksichtigen, wird der Abstand mit einem "
            "eingerechneten L\xe4ngenverh\xe4ltnis (WLG1/WLG2) angepasst."
            )
        self.canRunInBackground = True
        self.category = "DGM-W"

    def getParameterInfo(self):
        """Define parameter definitions for
        'CreateIntermediateCrossSections'.
         
        @param param0 in_cross_sections(DEFeatureClass):
            The input cross sections feature class. The parameter is
            filtered to 'Polyline'.
        @param param1 in_wlb(DEFeatureClass):
            The input water land border feature class. The parameter is
            filtered to 'Polyline'.
        @param param2 distance(GPDouble):
            The medium distance between successive cross lines. The
            default value is '10.0' meters. The parameter range is
            filtered from '1.0' meters to '50.0' meters.
        @param param3 workspace(DEWorkspace):
            Workspace for results. The parameter is filtered to 'Local
            Database'.
        @param param4 out_intermediate_cross_sections_name(GPString):
            The name of the feature class with the intermediate cross
            sections.
        @param param5 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
         
        """ 
        param0 = arcpy.Parameter(
            displayName="Querprofile (In cross sections)",
            name="in_cross_sections",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param0.filter.list = ["Polyline"]
        
        param1 = arcpy.Parameter(
            displayName="WLG /Uferlinien (In water land border)",
            name="in_wlb",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param1.filter.list = ["Polyline"]
        
        param2 = arcpy.Parameter(
            displayName="Abstand [m] (Distance[m])",
            name="distance",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input"
            )
        param2.value = 10.0
        param2.filter.type = "Range"
        param2.filter.list = [1.0, 50.0]
        
        param3 = arcpy.Parameter(
            displayName="Ausgabe-Geodatabase (Workspace)",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
            )
        param3.filter.list = ["Local Database"]
        
        param4 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der Zwischenprofile (Out "
                "intermediate cross sections name)"
                ),
            name="out_intermediate_cross_sections_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param5 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param5.value = True
         
        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        """Allow the tool to execute, only if the 'ArcGIS for Desktop
        Advanced' license is available.
        
        """
        try:
            if (arcpy.CheckProduct("arcinfo") != "AlreadyInitialized"
                    and arcpy.CheckProduct("arcinfo") != "Available"):
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("ArcGIS for Desktop Advanced license is unavailable.")
            return False

        return True
    
    def updateMessages(self, parameters):
        """Modify the messages created by internal parameter validation.
        
        This method is called after internal validation.
        
        """
        if (parameters[2].value and parameters[2].hasError()):
            parameters[2].setErrorMessage(
                "Zul\xe4ssiger Wertebereich liegt zwischen 1,0 - 50,0. "
                "Als Dezimaltrennzeichen bitte ',' verwenden."
                )
        
        return    

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. Then the 
        function create_cross_lines is called and executed to create
        the intermediate cross sections. Afterwards the direction is
        checked and if necessary corrected.
        
        """
        in_cross_sections = parameters[0].valueAsText
        in_wlb = parameters[1].valueAsText
        distance = parameters[2].value
        workspace = parameters[3].valueAsText
        out_intermediate_cross_sections_name = parameters[4].valueAsText
        overwrite_output = parameters[5].value
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        logger.info("Start function create_cross_lines.")
        element_count_method = ""
        remain_percentage = ""
        cross_lines = create_cross_lines(
            workspace, in_cross_sections, in_wlb, distance,
            out_intermediate_cross_sections_name, element_count_method,
            remain_percentage
            )
        logger.info("Create_cross_lines finished successfully.")
        
        logger.info(
            "Start function flip_line_direction to check and correct cross "
            "lines."
            )
        keep_names = True
        reference_where_clause = "WLBID = 1"
        out_features_name = ""
        flip_line_direction(
            workspace, cross_lines, in_wlb, out_features_name, keep_names,
            reference_where_clause
            )
        logger.info("Cross lines checked and flipped successfully.")
    
        return
    
    
class CreateLongitudinalSections(object):
    """Tool that creates longitudinal sections.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'CreateLongitudinalSections'."""
        self.label = "Erstelle L\xe4ngsprofile"
        self.description = (
            "Erstellt in einer festgelegten Anzahl (standardm\xe4\xdfig 8) "
            "L\xe4ngsprofile (Punkte und Linien) f\xfcr die "
            "H\xf6heninterpolation. Die Linien gelten dabei lediglich als "
            "\xfcberpr\xfcfung daf\xfcr, dass die Profile korrekt miteinander "
            "verbunden wurden."
            )
        self.canRunInBackground = True
        self.category = "DGM-W"

    def getParameterInfo(self):
        """Define parameter definitions for 'CreateLongitudinalSections'.
         
        @param param0 in_intermediate_cross_sections(DEFeatureClass):
            The input intermediate cross sections feature class. The 
            parameter is filtered to 'Polyline'.
        @param param1 count_longitudinal_sections(GPLong):
            The count of longitudinal sections which should be created.
            The default value is '8'. The parameter range is filtered
            from '3' to '50', because the water land border is already
            included.
        @param param2 workspace(DEWorkspace):
            Workspace for results. The parameter is filtered to 'Local
            Database'.
        @param param3 out_longitudinal_section_points_name(GPString):
            The name of the feature class with the longitudinal sections
            points.
        @param param4 out_longitudinal_section_lines_name(GPString):
            The name of the feature class with the longitudinal sections
            lines.
        @param param5 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
         
        """ 
        param0 = arcpy.Parameter(
            displayName="Zwischenprofile (In intermediate cross sections)",
            name="in_intermediate_cross_sections",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param0.filter.list = ["Polyline"]
        
        param1 = arcpy.Parameter(
            displayName="Anzahl L\xe4ngsprofile (count longitudinal sections)",
            name="count_longitudinal_sections",
            datatype="GPLong",
            parameterType="Required",
            direction="Input"
            )
        param1.value = 8
        param1.filter.type = "Range"
        param1.filter.list = [3, 50]
        
        param2 = arcpy.Parameter(
            displayName="Ausgabe-Geodatabase (Workspace)",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
            )
        param2.filter.list = ["Local Database"]
        
        param3 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der Punkte (Out longitudinal "
                "section points name)"
                ),
            name="out_longitudinal_section_points_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param4 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der Linien (Out longitudinal "
                "section lines name)"
                ),
            name="out_longitudinal_section_lines_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param5 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param5.value = True
         
        params = [param0, param1, param2, param3, param4, param5]
        return params

    def isLicensed(self):
        """Allow the tool to execute, only if the 'ArcGIS for Desktop
        Advanced' license is available.
        
        """
        try:
            if (arcpy.CheckProduct("arcinfo") != "AlreadyInitialized"
                    and arcpy.CheckProduct("arcinfo") != "Available"):
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("ArcGIS for Desktop Advanced license is unavailable.")
            return False

        return True
    
    def updateMessages(self, parameters):
        """Modify the messages created by internal parameter validation.
        
        This method is called after internal validation.
        
        """
        if (parameters[1].value and parameters[1].hasError()):
            parameters[1].setErrorMessage(
                "Zul\xe4ssiger Wertebereich liegt zwischen '3' - '50'."
                )
        
        return    

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. Then the 
        function create_longitudinal_sections is called and executed.
        
        """
        in_intermediate_cross_sections = parameters[0].valueAsText
        count_longitudinal_sections = parameters[1].value
        workspace = parameters[2].valueAsText
        out_longitudinal_section_points_name = parameters[3].valueAsText
        out_longitudinal_section_lines_name = parameters[4].valueAsText
        overwrite_output = parameters[5].value
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        logger.info("Start function create_longitudinal_sections.")
        create_longitudinal_sections(
            workspace, in_intermediate_cross_sections,
            count_longitudinal_sections, out_longitudinal_section_points_name, 
            out_longitudinal_section_lines_name)
        logger.info("Create_longitudinal_sections finished successfully.")
    
        return
    
    
class InterpolateLongitudinalSections(object):
    """Tool that interpolates the longitudinal sections height values.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'InterpolateLongitudinalSections'."""
        self.label = "Interpoliere L\xe4ngsprofile"
        self.description =  (
            "Interpoliert die H\xf6henwerte der L\xe4ngsprofile. Dazu werden "
            "zun\xe4chst die H\xf6henwerte der Punkte der Querprofile auf die "
            "Punkte der L\xe4ngsprofile \xfcbertragen. Anschlie\xdfend werden "
            "die Punkte der L\xe4ngsprofile zwischen zwei aufeinander "
            "folgenden Querprofilen interpoliert." 
            )
        self.canRunInBackground = True
        self.category = "DGM-W"

    def getParameterInfo(self):
        """Define parameter definitions for 
        'InterpolateLongitudinalSections'.
        
        @param param0 in_longitudinal_section_points(DEFeatureClass):
            The input longitudinal section points feature class. The 
            parameter is filtered to 'Point'.
        @param param1 in_longitudinal_section_lines(DEFeatureClass):
            The input longitudinal section lines feature class. The 
            parameter is filtered to 'Polyline'.   
        @param param2 in_cross_section_points(DEFeatureClass):
            The input cross section points feature class. The parameter
            is filtered to 'Point'.
        @param param3 in_cross_section_lines(DEFeatureClass):
            The input cross section lines feature class. The parameter
            parameter is filtered to 'Polyline'.
        @param param4 height_assignment_method(GPString):
            The height assignment method. The default value is
            'NEAR_INSIDE_WLB'. The parameter is filtered to 'NEAR_ALL'
            and 'NEAR_INISIDE_WLB'.
        @param param5 interpolation_method(GPString):
            The height interpolation method. The default value is
            'LINEAR'. The parameter is filtered to 'LINEAR'.
        @param param6 keep_names(GPBoolean):
            Keep_names? The default value is 'True'.
        @param param7 workspace(DEWorkspace):
            Workspace for results. The parameter is filtered to 'Local
            Database'.
        @param param8 out_longitudinal_sections_name(GPString): 
            The name of the feature class with the interpolated
            longitudinal sections.
        @param param9 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
        
        """ 
        param0 = arcpy.Parameter(
            displayName=(
                "L\xe4ngsprofile Punkte (In longitudinal section points)"
                ),
            name="in_longitudinal_section_points",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param0.filter.list = ["Point"]
        
        param1 = arcpy.Parameter(
            displayName=(
                "L\xe4ngsprofile Linien (In longitudinal section lines)"
                ),
            name="in_longitudinal_section_lines",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param1.filter.list = ["Polyline"]
            
        param2 = arcpy.Parameter(
            displayName="Querprofile Punkte (In cross section points)",
            name="in_cross_section_points",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param2.filter.list = ["Point"]
        
        param3 = arcpy.Parameter(
            displayName="Querprofile Linien (In cross section lines)",
            name="in_cross_section_lines",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param3.filter.list = ["Polyline"]
        
        param4 = arcpy.Parameter(
            displayName=(
                "H\xf6hen\xfcbertragungsmethode (Height assignment method)"
                ),
            name="height_assignment_method",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        param4.value = "NEAR_INSIDE_WLB"
        param4.filter.type = "ValueList"
        param4.filter.list = ["NEAR_ALL", "NEAR_INSIDE_WLB"]
        
        param5 = arcpy.Parameter(
            displayName="Interpolationsmethode (Interpolation method)",
            name="interpolation_method",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        param5.value = "LINEAR"
        param5.filter.type = "ValueList"
        param5.filter.list = ["LINEAR"]
        
        param6 = arcpy.Parameter(
            displayName=(
                "Namen behalten: Ausgangsdaten = Eingangsdaten? (keep names: "
                "output names = input names?)"
                ),
            name="keep_names",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param6.value = True 
        
        param7 = arcpy.Parameter(
            displayName="Ausgabe-Geodatabase (Workspace)",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input"
            )
        param7.filter.list = ["Local Database"]
        
        param8 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der interpolierten "
                " L\xe4ngsprofile (Out interpolated longitudinal sections "
                "name)"
                ),
            name="out_longitudinal_sections_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param9 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param9.value = True
         
        params = [
            param0, param1, param2, param3, param4, param5, param6, param7,
            param8, param9
            ]
        
        return params

    def isLicensed(self):
        """Allow the tool to execute, only if the 'ArcGIS for Desktop
        Advanced' license is available.
        
        """
        try:
            if (arcpy.CheckProduct("arcinfo") != "AlreadyInitialized"
                    and arcpy.CheckProduct("arcinfo") != "Available"):
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("ArcGIS for Desktop Advanced license is unavailable.")
            return False

        return True
    
    def updateParameters(self, parameters):
        """Modify the values, properties and display of parameters.
        
        This method is called whenever a parameter has been changed.
        
        """ 
        if parameters[6].value:
            parameters[7].enabled = False
            parameters[8].enabled = False
            parameters[9].enabled = False
            parameters[9].value = True
        else:
            parameters[7].enabled = True
            parameters[8].enabled = True
            parameters[9].enabled = True

        return
    
    def updateMessages(self, parameters):
        """Modify the messages created by internal parameter validation.
        
        This method is called after internal validation.
        
        """
        if not parameters[6].value:
            if not parameters[7].value:
                parameters[7].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[8].value:
                parameters[8].setErrorMessage("Eingabewert erforderlich.")
        
        if (parameters[4].value and parameters[4].hasError()):
            parameters[4].setErrorMessage(
                "Zul\xe4ssige Werte: 'NEAR_ALL', 'NEAR_INSIDE_WLB'."
                )
            
        if (parameters[5].value and parameters[5].hasError()):
            parameters[5].setErrorMessage("Zul\xe4ssige Werte: 'LINEAR'.")
        
        return

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. Then the 
        function interpolate_longitudinal_sections is called and
        executed.
        
        """
        in_longitudinal_section_points = parameters[0].valueAsText
        in_longitudinal_section_lines = parameters[1].valueAsText
        in_cross_section_points = parameters[2].valueAsText
        in_cross_section_lines = parameters[3].valueAsText
        height_assignment_method = parameters[4].valueAsText
        interpolation_method = parameters[5].valueAsText
        keep_names = parameters[6].value
        workspace = parameters[7].valueAsText
        out_longitudinal_sections_name = parameters[8].valueAsText
        overwrite_output = parameters[9].value
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        logger.info("Start function interpolate_longitudinal_sections.")
        interpolate_longitudinal_sections(
            workspace, in_longitudinal_section_points, 
            in_longitudinal_section_lines, in_cross_section_points,
            in_cross_section_lines, height_assignment_method, 
            interpolation_method, out_longitudinal_sections_name,
            keep_names
            )
        logger.info("Interpolate_longitudinal_sections finished successfully.")
        
        return

    
class CreateDTMW(object):
    """Tool that creates the digital terrain model of the watercourse.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'CreateDTMW'."""
        self.label = "Erstelle DGM-W"
        self.description = (
            "Erstellt aus den Interpolierten H\xf6henpunkten des Flusslaufs "
            "und dem DGM des Vorlands das DGM-W. Dabei werden die Punkte des "
            "DGM, die innerhalb des Gew\xe4sserpolygons liegen gel\xf6scht "
            "und durch die interpolierten H\xf6henpunkte ersetzt. Um die "
            "Punktmenge zu reduzieren, kann um den Fluss ein Puffer gelegt "
            "werden. Alle au\xdferhalb dieses Puffers liegenden Punkte werden "
            "gel\xf6scht."
            )
        self.canRunInBackground = True
        self.category = "DGM-W"

    def getParameterInfo(self):
        """Define parameter definitions for 'CreateDTMW'.
        
        @param param0 in_dtm_channel(DEFeatureClass):
            The input digital terrain model of the channel feature
            class. The parameter is filtered to 'Point'.
        @param param1 load_dtm_foreshore(GPBoolean):
            Load digital terrain model of the foreshore? The default
            value is 'True'.
        @param param2 in_dtm_foreshore_points(DEFile):
            File which contains the digital terrain model of the
            foreshore points. The parameter is multivalue and filtered
            to 'txt', 'csv' and 'xyz'.
        @param param3 out_dtm_foreshore_name(GPString): 
            Name of the feature class with the digital terrain model of
            the foreshore.
        @param param4 spatial_reference(GPSpatialReference):
            Spatial reference system, e.g. as epsg-code.
        @param param5 in_x_field(GPString):
            The input x field.
        @param param6 in_y_field(GPString):
            The input y field.
        @param param7 in_z_field(GPString):
            The input z field.
        @param param8 decimal_separator(GPString):
            The decimal separator. The default value is 'DECIMAL_POINT'.
            The parameter is filtered to 'DECIMAL_POINT' and
            'DECIMAL_COMMA'.
        @param param9 in_dtm_foreshore(DEFeatureClass):
            The input digital terrain model of the foreshore feature
            class. The parameter is filterd to 'Point'.
        @param param10 in_stream_polygon(DEFeatureClass):
            The input stream polygon feature class. The parameter is 
            filtered to 'Polygon'.
        @param param11 workspace(DEWorkspace):
            Workspace for results. The parameter is filtered to 'Local
            Database'.
        @param param12 out_dtm_watercourse_name(GPString): 
            Name of the feature class with the digital terrain model of
            the watercourse.
        @param param13 reduce_point_set(GPBoolean):
            Reduce point set? The default value is 'False'.  
        @param param14 buffer_distance(GPDouble):
            The buffer distance to reduce the point set. The default
            value is '500.0' meters. The parameter range is filtered 
            from '1.0' meters to '1000.0' meters.     
        @param param15 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
        
        """ 
        param0 = arcpy.Parameter(
            displayName=(
                "DGM der Flusssohle mit den interpolierten H\xf6henpunkten "
                "(In ditgital terrain model of the channel with interpolated "
                "height (z) values"
                ),
            name="in_dtm_channel",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param0.filter.list = ["Point"]
        
        param1 = arcpy.Parameter(
            displayName=(
                "DGM des Vorlands einladen? (Load the digital terrain model "
                "of the foreshore?)"
                ),
            name="load_dtm_foreshore",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param1.value = True
        
        param2 = arcpy.Parameter(
            displayName=(
                "Punktdateien des Vorland-DGMs (In digital terrain model of "
                "the foreshore points)"
                ),
            name="in_dtm_foreshore_points",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
            multiValue=True
            )
        param2.filter.list = ["txt", "csv", "xyz"]
                    
        param3 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class des Vorland-DGMs (Out digital "
                "terrain model of the foreshore name)"
                ),
            name="out_dtm_foreshore_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param4 = arcpy.Parameter(
            displayName="SpatialReference (EPSG)",
            name="spatial_reference",
            datatype="GPSpatialReference",
            parameterType="Optional",
            direction="Input"
            )
        
        param5 = arcpy.Parameter(
            displayName="X-Feld (In x field)",
            name="in_x_field",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param6 = arcpy.Parameter(
            displayName="Y-Feld (In y field)",
            name="in_y_field",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )

        param7 = arcpy.Parameter(
            displayName="Z-Feld (In z field)",
            name="in_z_field",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param8 = arcpy.Parameter(
            displayName="Dezimaltrennzeichen (Decimal separator xyz files)",
            name="decimal_separator",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        param8.value = "DECIMAL_POINT"
        param8.filter.type = "ValueList"
        param8.filter.list = ["DECIMAL_POINT", "DECIMAL_COMMA"]
        
        param9 = arcpy.Parameter(
            displayName=(
                "DGM des Vorlands Feature-Class (In digital terrain model of "
                "the foreshore)"
                ),
            name="in_dtm_foreshore",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input"
            )
        param9.filter.list = ["Point"]
        
        param10 = arcpy.Parameter(
            displayName="Gew\xe4sserpolygon (In stream polygon)",
            name="in_stream_polygon",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param10.filter.list = ["Polygon"]
        
        param11 = arcpy.Parameter(
            displayName="Ausgabe-Geodatabase (Workspace)",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
            )
        param11.filter.list = ["Local Database"]
        
        param12 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class des DGM-W (Out digital "
                "terrain model of the watercourse name)"
                ),
            name="out_dtm_watercourse_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param13 = arcpy.Parameter(
            displayName=(
                "Punktmenge durch Puffer reduzieren? (Reduce point set with "
                "buffer?)"
                ),
            name="reduce_point_set",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param13.value = False
        
        param14 = arcpy.Parameter(
            displayName="Pufferdistanz [m] (Buffer distance [m])",
            name="buffer_distance",
            datatype="GPDouble",
            parameterType="Optional",
            direction="Input"
            )
        param14.value = 500.0
        param14.filter.type = "Range"
        param14.filter.list = [1.0, 1000.0]
        
        param15 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param15.value = True
         
        params = [
            param0, param1, param2, param3, param4, param5, param6, param7,
            param8, param9, param10, param11, param12, param13, param14, 
            param15
            ]
        
        return params

    def isLicensed(self):
        """Allow the tool to execute, only if the extension 'ArcGIS 3D
        Analyst' is available.
        
        """
        try:
            if arcpy.CheckExtension("3D") != "Available":
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("Extension '3D Analyst' is unavailable.")
            return False

        return True

    def updateParameters(self, parameters):
        """Modify the values, properties and display of parameters.
        
        This method is called whenever a parameter has been changed.
        
        """ 
        if parameters[1].value:
            parameters[2].enabled = True
            parameters[3].enabled = True
            parameters[4].enabled = True
            parameters[5].enabled = True
            parameters[6].enabled = True
            parameters[7].enabled = True
            parameters[8].enabled = True
            parameters[9].enabled = False
        else:
            parameters[2].enabled = False
            parameters[3].enabled = False
            parameters[4].enabled = False
            parameters[5].enabled = False
            parameters[6].enabled = False
            parameters[7].enabled = False
            parameters[8].enabled = False
            parameters[9].enabled = True
        
        if (parameters[1].value and parameters[2].value):
            extensions = []
            in_files = parameters[2].valueAsText
            in_files = in_files.split(";")
            for in_file in in_files:
                desc = arcpy.Describe(in_file)
                extensions.append(desc.extension)
            if (("csv" in extensions or "txt" in extensions)
                    and "xyz" not in extensions):
                parameters[5].enabled = True
                parameters[6].enabled = True
                parameters[7].enabled = True
                parameters[8].enabled = False
            elif (("csv" in extensions or "txt" in extensions)
                    and "xyz" in extensions):
                parameters[5].enabled = True
                parameters[6].enabled = True
                parameters[7].enabled = True
                parameters[8].enabled = True
            elif ("csv" not in extensions and "txt" not in extensions
                    and "xyz" in extensions):
                parameters[5].enabled = False
                parameters[6].enabled = False
                parameters[7].enabled = False
                parameters[8].enabled = True
            
        if parameters[13].value:
            parameters[14].enabled = True
        else:
            parameters[14].enabled = False
        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal parameter validation.
        
        This method is called after internal validation.
        
        """
        if (not parameters[1].value and not parameters[9].value):
            parameters[9].setErrorMessage("Eingabewert erforderlich.")
        elif parameters[1].value:
            if not parameters[2].value:
                parameters[2].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[3].value:
                parameters[3].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[4].value:
                parameters[4].setErrorMessage("Eingabewert erforderlich.")
            if parameters[2].value:
                extensions = []
                in_files = parameters[2].valueAsText
                in_files = in_files.split(";")
                for in_file in in_files:
                    desc = arcpy.Describe(in_file)
                    extensions.append(desc.extension)
                if ("csv" in extensions or "txt" in extensions):
                    if not parameters[5].value:
                        parameters[5].setErrorMessage(
                            "Eingabewert erforderlich."
                            )                    
                    if not parameters[6].value:
                        parameters[6].setErrorMessage(
                            "Eingabewert erforderlich."
                            )
                    if not parameters[7].value:
                        parameters[7].setErrorMessage(
                            "Eingabewert erforderlich."
                            )
                if "xyz" in extensions:
                    if not parameters[8].value:
                        parameters[8].setErrorMessage(
                            "Eingabewert erforderlich."
                            )
        
        if (parameters[13].value and not parameters[14].value):
            parameters[14].setErrorMessage("Eingabewert erforderlich.")
            
        if (parameters[14].value and parameters[14].hasError()):
            parameters[14].setErrorMessage(
                "Zul\xe4ssiger Wertebereich liegt zwischen 1,0 - 1000,0. "
                "Als Dezimaltrennzeichen bitte ',' verwenden."
                )
          
        if (parameters[8].value and parameters[8].hasError()):
            parameters[8].setErrorMessage(
                "Zul\xe4ssige Werte: 'DECIMAL_POINT', 'DECIMAL_COMMA'."
                )
        
        return

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. If 
        load_dtm_foreshore is 'True', the function 
        convert_spatial_reference is called and executed. Afterwards the
        function load_points_from_multiple files is called and executed. 
        Then the function create_dtmw is called and executed to create 
        the digital terrain model of the watercourse. 
        
        """
        in_dtm_channel = parameters[0].valueAsText
        load_dtm_foreshore = parameters[1].value
        in_dtm_foreshore_points = parameters[2].valueAsText
        out_dtm_foreshore_name = parameters[3].valueAsText
        spatial_reference = parameters[4].valueAsText
        in_x_field = parameters[5].valueAsText
        in_y_field = parameters[6].valueAsText
        in_z_field = parameters[7].valueAsText
        decimal_separator = parameters[8].valueAsText
        in_dtm_foreshore = parameters[9].valueAsText
        in_stream_polygon = parameters[10].valueAsText
        workspace = parameters[11].valueAsText
        out_dtm_watercourse_name = parameters[12].valueAsText
        reduce_point_set = parameters[13].value
        buffer_distance = parameters[14].value
        overwrite_output = parameters[15].value
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        if load_dtm_foreshore:
            logger.info("Start function convert_spatial_reference.")
            spatial_reference = convert_spatial_reference(spatial_reference)
            logger.info("Convert_spatial_reference finished successfully.")
            
            logger.info("Start function load_points_from_multiple_files.")
            in_dtm_foreshore = load_points_from_multiple_files(
                workspace, in_dtm_foreshore_points, out_dtm_foreshore_name, 
                spatial_reference, in_x_field, in_y_field, in_z_field,
                decimal_separator
                )
            logger.info(
                "Load_points_from_multiple_files finished successfully."
                )

        logger.info("Start function create_dtmw.")
        create_dtmw(
            workspace, in_dtm_channel, in_dtm_foreshore, in_stream_polygon, 
            out_dtm_watercourse_name, reduce_point_set, buffer_distance
            )
        logger.info("Create_dtmw finished successfully.")
        
        return
    
    
class ExportFeatures(object):
    """Tool that exports the input features in different formats.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'ExportFeatures'."""
        self.label = "Exportiere Features"
        self.description = (
            "Die Eingabe - Features k\xf6nnen in verschiedene Formate "
            "(Feature Class, ESRI Shape, ASCII (xyz) oder AutoCAD-DXF) "
            "exportiert werden."
            )
        self.canRunInBackground = True
        self.category = "Export"

    def getParameterInfo(self):
        """Define parameter definitions for 'ExportFeatures'.
        
        @param param0 in_features(DEFeatureClass):
            The input feature class which should be exported.
        @param param1 export_to_feature_class(GPBoolean):
            Export features to feature class? The default value is 
            'False'.
        @param param2 export_to_esri_shape(GPBoolean):
            Export features to esri shape? The default value is 'False'.
        @param param3 export_to_ascii_xyz(GPBoolean):
            Export features to ascii xyz? The default value is 'False'.
        @param param4 export_to_autocad(GPBoolean):
            Export features to autocad? The default value is 'False'.
        @param param5 out_directory(DEFolder):
            Directory which will contain the output files.
        @param param6 out_name(GPString): 
            Name of the outputs.  
        @param param7 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
        @param param8 fields(GPString):
            Add displayed fields to output. The parameter is multivalue 
            and only available if the export type is ascii xyz.
        @param param9 autocad_type(GpString)
            The autocad_type. The parameter is filterd to 'DGN_V8',
            'DWG_R14', 'DWG_R2000', 'DWG_R2004', 'DWG_R2005',
            'DWG_R2007', 'DWG_R2010', 'DWG_R2013', 'DXF_R14',
            'DXF_R2000', 'DXF_R2004', 'DXF_R2005', 'DXF_R2007',
            'DXF_R2010' and 'DXF_R2013'. The default value is 
            'DXF_R2013'. The parameter is only available if the export
            type is autocad.
        
        """ 
        param0 = arcpy.Parameter(
            displayName="Eingabe Feature Class (In feature class)",
            name="in_features",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        
        param1 = arcpy.Parameter(
            displayName="Export in Feature Class? (Export to feature class?)",
            name="export_to_feature_class",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param1.value = False
        
        param2 = arcpy.Parameter(
            displayName="Export in ESRI Shape? (Export to Esri Shape?)",
            name="export_to_esri_shape",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param2.value = False
        
        param3 = arcpy.Parameter(
            displayName="Export in ASCII xyz? (Export to ascii xyz)?",
            name="export_to_ascii_xyz",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param3.value = False
        
        param4 = arcpy.Parameter(
            displayName="Export in AutoCAD? (Export to autocad?)",
            name="export_to_autocad",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param4.value = False
        
        param5 = arcpy.Parameter(
            displayName="Ausgabeverzeichnis (Out directory)",
            name="out_directory",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
            )
                    
        param6 = arcpy.Parameter(
            displayName=(
                "Ausgabename f\xfcr Ordner und Dateien (Out folder and file "
                "name)"
                ),
            name="out_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param7 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param7.value = True
        
        param8 = arcpy.Parameter(
            displayName=(
                "Felder zur Ausgabe hinzuf\xfcgen (Add fields to output)"
                ),
            name="fields",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True
            )
        
        param9 = arcpy.Parameter(
            displayName="AutoCad-Format (Autocad type)",
            name="autocad_type",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        param9.value = "DXF_R2013"
        param9.filter.type = "ValueList"
        param9.filter.list = [
            "DGN_V8", "DWG_R14", "DWG_R2000", "DWG_R2004", "DWG_R2005", 
            "DWG_R2007", "DWG_R2010", "DWG_R2013", "DXF_R14", "DXF_R2000",
            "DXF_R2004", "DXF_R2005", "DXF_R2007", "DXF_R2010", "DXF_R2013"
            ]
         
        params = [
            param0, param1, param2, param3, param4, param5, param6, param7,
            param8, param9
            ]
        
        return params

    def isLicensed(self):
        """Allow the tool to execute always."""
        return True

    def updateParameters(self, parameters):
        """Modify the values, properties and display of parameters.
        
        This method is called whenever a parameter has been changed.
        
        """ 
        if parameters[3].value:
            parameters[0].filter.list = ["Point"]
            if parameters[0].value:
                field_names = list_field_names(parameters[0].valueAsText)
                parameters[8].filter.list = field_names
                parameters[8].enabled = True
        else:
            parameters[0].filter.list = []
            parameters[8].enabled = False
        
        if parameters[4].value:
            parameters[9].enabled = True
        else:
            parameters[9].enabled = False
        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal parameter validation.
        
        This method is called after internal validation.
        
        """
        if (not parameters[1].value and not parameters[2].value
                and not parameters[3].value and not parameters[4].value):
            parameters[1].setErrorMessage(
                "Keine Exportvariante ausgew\xe4hlt."
                )
            parameters[2].setErrorMessage(
                "Keine Exportvariante ausgew\xe4hlt."
                )
            parameters[3].setErrorMessage(
                "Keine Exportvariante ausgew\xe4hlt."
                )
            parameters[4].setErrorMessage(
                "Keine Exportvariante ausgew\xe4hlt."
                )
            
        if (parameters[3].value and parameters[0].hasError()):
            parameters[0].setErrorMessage(
                "Keine Punkt-Feature_Class ausgew\xe4hlt."
                )
        
        if (parameters[4].value and not parameters[9].value):
            parameters[9].setErrorMessage("Kein AutoCad-Format ausgew\xe4hlt.")
            
        if (parameters[9].value and parameters[9].hasError()):
            parameters[9].setErrorMessage(
                "Zul\xe4ssige Eingabetypen: 'DGN_V8', 'DWG_R14', 'DWG_R2000', "
                "'DWG_R2004', 'DWG_R2005', 'DWG_R2007', 'DWG_R2010', "
                "'DWG_R2013', 'DXF_R14', 'DXF_R2000', 'DXF_R2004', "
                "'DXF_R2005', 'DXF_R2007', 'DXF_R2010' oder 'DXF_R2013'."
                )
        
        return

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. Then the 
        output path is checked and created if necessary. Depending on
        which export formats are chosen, the respective functions are
        called and executed.
        
        """
        in_features = parameters[0].valueAsText
        export_to_feature_class = parameters[1].value
        export_to_esri_shape = parameters[2].value
        export_to_ascii_xyz = parameters[3].value
        export_to_autocad = parameters[4].value
        out_directory = parameters[5].valueAsText
        out_name = parameters[6].valueAsText
        overwrite_output = parameters[7].value
        fields = parameters[8].valueAsText
        autocad_type = parameters[9].valueAsText
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        logger.info("Check and if necessary create output path.")
        out_path = out_directory + "/" + out_name
        if not arcpy.Exists(out_path):
            arcpy.CreateFolder_management(out_directory, out_name)
        elif (not overwrite_output and arcpy.Exists(out_path)):
            logger.warning(
                "Output path " + out_path + "already exists. Change output "
                "path: " + out_path + time.strftime("%d%m%y_%H%M%S")
                )
            out_name = out_name + time.strftime("%d%m%y_%H%M%S")
                
            arcpy.CreateFolder_management(out_directory, out_name)
            out_path = out_path + time.strftime("%d%m%y_%H%M%S")
        logger.info(
            "Output path created successfully. The output path is " + out_path
            )
           
        if export_to_feature_class:
            logger.info("Start function export_features_to_feature_class.")
            export_features_to_feature_class(in_features, out_path, out_name)
            logger.info(
                "Export_features_to_feature_class finished successfully."
                )
            
        if export_to_esri_shape:
            logger.info("Start function export_features_to_esri_shape.")
            export_features_to_esri_shape(in_features, out_path, out_name)
            logger.info("Export_features_to_esri_shape finished successfully.")
            
        if export_to_ascii_xyz:
            logger.info("Start function export_features_to_ascii_xyz.")
            export_features_to_ascii_xyz(
                in_features, out_path, out_name, fields
                )
            logger.info("Export_features_to_ascii_xyz finished successfully.")
            
        if export_to_autocad:
            logger.info("Start function export_features_to_autocad.")
            export_features_to_autocad(
                in_features, out_path, out_name, autocad_type
                )
            logger.info(
                "Export_features_to_autocad finished successfully."
                )
        return
    

class CreateTIN(object):
    """Tool that creates a triangulated irregular network.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'CreateTIN'."""
        self.label = "Erstelle TIN"
        self.description = (
            "Erstellt ein TIN aus Punktdateien (triangulated irregular "
            "network). Bei den Punktdateien kann es sich zum Beispiel um das "
            "DGM-W handeln."
            )
        self.canRunInBackground = True
        self.category = "Export"

    def getParameterInfo(self):
        """Define parameter definitions for 'CreateTIN'.
        
        @param param0 in_tin_points(DEFeatureClass):
            The input points for the triangulated irregular network. The
            parameter is filtered to 'Point'.
        @param param1 load_tin_points(GPBoolean):
            Load input points from file? The default value is 'False'.
        @param param2 in_tin_point_files(DEFile):
            File which contains the input points for the triangulated
            irregular network. The parameter is multivalue and filtered
            to 'txt', 'csv' and 'xyz'.
        @param param3 out_tin_points_name(GPString): 
            Name of the feature class with the loaded points.
        @param param4 spatial_reference(GPSpatialReference):
            Spatial reference system, e.g. as epsg-code. The default
            value is '25832' (epsg-code).
        @param param5 in_x_field(GPString):
            The input x field.
        @param param6 in_y_field(GPString):
            The input y field.
        @param param7 in_z_field(GPString):
            The input z field.
        @param param8 decimal_separator(GPString):
            The decimal separator. The default value is 'DECIMAL_COMMA'.
            The parameter is filtered to 'DECIMAL_POINT' and
            'DECIMAL_COMMA'.
        @param param9 workspace(DEWorkspace):
            Workspace for feature class results. The parameter is 
            filtered to 'Local Database'.
        @param param10 out_directory(DEFolder):
            Directory which will contain the output files.
        @param param11 out_tin_name(GPString): 
            Name of the output triangulated irregular network.
        @param param12 triangulation technique(GPString): 
            The triangulation technique. The possible values are 
            'DELAUNAY' and 'CONSTRAINED_DELAUNAY'. The default value is
            'DELAUNAY'. 
        @param param13 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
        
        """ 
        param0 = arcpy.Parameter(
            displayName=(
                "TIN-Punkte Feature-Class (In triangulated irregular network "
                "point feature class.)"
                ),
            name="in_tin_points",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input"
            )
        param0.filter.list = ["Point"]
        
        param1 = arcpy.Parameter(
            displayName=(
                "TIN-Punktdateien einladen? (Load triangulated irregular "
                "network points from file?)"
                ),
            name="load_tin_points",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param1.value = False
        
        param2 = arcpy.Parameter(
            displayName=(
                "TIN-Punktdateien (In triangulted irregular network point "
                "files)"
                ),
            name="in_tin_point_files",
            datatype="DEFile",
            parameterType="Optional",
            direction="Input",
            multiValue=True
            )
        param2.filter.list = ["txt", "csv", "xyz"]
                    
        param3 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der TIN-Punkte (Out "
                "triangulated irregular network points name)"
                ),
            name="out_tin_points_name",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param4 = arcpy.Parameter(
            displayName="SpatialReference (EPSG)",
            name="spatial_reference",
            datatype="GPSpatialReference",
            parameterType="Optional",
            direction="Input"
            )
        param4.value = 25832 
        
        param5 = arcpy.Parameter(
            displayName="X-Feld (In x field)",
            name="in_x_field",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param6 = arcpy.Parameter(
            displayName="Y-Feld (In y field)",
            name="in_y_field",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )

        param7 = arcpy.Parameter(
            displayName="Z-Feld (In z field)",
            name="in_z_field",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        
        param8 = arcpy.Parameter(
            displayName="Dezimaltrennzeichen (Decimal separator xyz files)",
            name="decimal_separator",
            datatype="GPString",
            parameterType="Optional",
            direction="Input"
            )
        param8.value = "DECIMAL_COMMA"
        param8.filter.type = "ValueList"
        param8.filter.list = ["DECIMAL_POINT", "DECIMAL_COMMA"]
        
        param9 = arcpy.Parameter(
            displayName="Ausgabe-Geodatabase (Workspace)",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Optional",
            direction="Input"
            )
        param9.filter.list = ["Local Database"]
        
        param10 = arcpy.Parameter(
            displayName="Ausgabeverzeichnis (Out directory)",
            name="out_directory",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
            )
                    
        param11 = arcpy.Parameter(
            displayName=(
                "Ausgabename TIN (Out triangulated irregular network name)"
                ),
            name="out_tin_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param12 = arcpy.Parameter(
            displayName="Triangulationstechnik (Triangulation technique)",
            name="triangulation_technique",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        param12.value = "DELAUNAY"
        param12.filter.type = "ValueList"
        param12.filter.list = ["DELAUNAY", "CONSTRAINED_DELAUNAY"]
        
        param13 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param13.value = True
         
        params = [
            param0, param1, param2, param3, param4, param5, param6, param7,
            param8, param9, param10, param11, param12, param13,
            ]
        
        return params

    def isLicensed(self):
        """Allow the tool to execute, only if the extension 'ArcGIS 3D
        Analyst' is available.
        
        """
        try:
            if arcpy.CheckExtension("3D") != "Available":
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("Extension '3D Analyst' is unavailable.")
            return False

        return True

    def updateParameters(self, parameters):
        """Modify the values, properties and display of parameters.
        
        This method is called whenever a parameter has been changed.
        
        """ 
        if parameters[1].value:
            parameters[0].enabled = False
            parameters[2].enabled = True
            parameters[3].enabled = True
            parameters[4].enabled = True
            parameters[5].enabled = True
            parameters[6].enabled = True
            parameters[7].enabled = True
            parameters[8].enabled = True
            parameters[9].enabled = True
        else:
            parameters[0].enabled = True
            parameters[2].enabled = False
            parameters[3].enabled = False
            parameters[4].enabled = False
            parameters[5].enabled = False
            parameters[6].enabled = False
            parameters[7].enabled = False
            parameters[8].enabled = False
            parameters[9].enabled = False
        
        if (parameters[1].value and parameters[2].value):
            extensions = []
            in_files = parameters[2].valueAsText
            in_files = in_files.split(";")
            for in_file in in_files:
                desc = arcpy.Describe(in_file)
                extensions.append(desc.extension)
            if (("csv" in extensions or "txt" in extensions)
                    and "xyz" not in extensions):
                parameters[5].enabled = True
                parameters[6].enabled = True
                parameters[7].enabled = True
                parameters[8].enabled = False
            elif (("csv" in extensions or "txt" in extensions)
                    and "xyz" in extensions):
                parameters[5].enabled = True
                parameters[6].enabled = True
                parameters[7].enabled = True
                parameters[8].enabled = True
            elif ("csv" not in extensions and "txt" not in extensions
                    and "xyz" in extensions):
                parameters[5].enabled = False
                parameters[6].enabled = False
                parameters[7].enabled = False
                parameters[8].enabled = True
        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal parameter validation.
        
        This method is called after internal validation.
        
        """
        if (not parameters[1].value and not parameters[0].value):
            parameters[0].setErrorMessage("Eingabewert erforderlich.")
        elif parameters[1].value:
            if not parameters[2].value:
                parameters[2].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[3].value:
                parameters[3].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[4].value:
                parameters[4].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[9].value:
                parameters[9].setErrorMessage("Eingabewert erforderlich.")
            if parameters[2].value:
                extensions = []
                in_files = parameters[2].valueAsText
                in_files = in_files.split(";")
                for in_file in in_files:
                    desc = arcpy.Describe(in_file)
                    extensions.append(desc.extension)
                if ("csv" in extensions or "txt" in extensions):
                    if not parameters[5].value:
                        parameters[5].setErrorMessage(
                            "Eingabewert erforderlich."
                            )                    
                    if not parameters[6].value:
                        parameters[6].setErrorMessage(
                            "Eingabewert erforderlich."
                            )
                    if not parameters[7].value:
                        parameters[7].setErrorMessage(
                            "Eingabewert erforderlich."
                            )
                if "xyz" in extensions:
                    if not parameters[8].value:
                        parameters[8].setErrorMessage(
                            "Eingabewert erforderlich."
                            )
          
        if (parameters[8].value and parameters[8].hasError()):
            parameters[8].setErrorMessage(
                "Zul\xe4ssige Werte: 'DECIMAL_POINT', 'DECIMAL_COMMA'."
                )
            
        if (parameters[12].value and parameters[12].hasError()):
            parameters[12].setErrorMessage(
                "Zul\xe4ssige Werte: 'DELAUNAY', 'CONSTRAINED_DELAUNAY'."
                )
        
        return

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. If 
        load_tin_points is 'True', the function convert_spatial_reference
        is called and executed. Afterwards the function
        load_points_from_multiple files is called and executed. Then 
        the function create_tin is called and executed to create the
        triangulated irregular network
        
        """
        in_tin_points = parameters[0].valueAsText
        load_tin_points = parameters[1].value
        in_tin_point_files = parameters[2].valueAsText
        out_tin_points_name = parameters[3].valueAsText
        spatial_reference = parameters[4].valueAsText
        in_x_field = parameters[5].valueAsText
        in_y_field = parameters[6].valueAsText
        in_z_field = parameters[7].valueAsText
        decimal_separator = parameters[8].valueAsText
        workspace = parameters[9].valueAsText
        out_directory = parameters[10].valueAsText
        out_tin_name = parameters[11].valueAsText
        triangulation_technique = parameters[12].valueAsText
        overwrite_output = parameters[13].value
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        if load_tin_points:
            logger.info("Start function convert_spatial_reference.")
            spatial_reference = convert_spatial_reference(spatial_reference)
            logger.info("Convert_spatial_reference finished successfully.")
            
            logger.info("Start function load_points_from_multiple_files.")
            in_tin_points = load_points_from_multiple_files(
                workspace, in_tin_point_files, out_tin_points_name, 
                spatial_reference, in_x_field, in_y_field, in_z_field,
                decimal_separator)
            logger.info(
                "Load_points_from_multiple_files finished successfully."
                )

        logger.info("Start function create_tin.")
        create_tin(
            in_tin_points, out_directory, out_tin_name, triangulation_technique
            )
        logger.info("Create_tin finished successfully.")
        
        return
    
    
class CreateVertices(object):
    """Tool that creates the vertices for the channel mesh.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'CreateVertices'."""
        self.label = "Erstelle St\xfctzpunkte"
        self.description = (
            "Erstellt die St\xfctzpunkte f\xfcr das Berechnungsnetz. Dazu "
            "werden in Abh\xe4ngigkeit der Breite der aktuellen St\xfctzlinie "
            "(erste St\xfctzlinie = erstes Querprofil) die Anzahl der "
            "St\xfctzpunkte f\xfcr diese bestimmt. Abh\xe4ngig von der Anzahl "
            "und demnach dem Abstand zwischen zwei St\xfctzpunkten wird der "
            "Abstand f\xfcr die n\xe4chste St\xfctzlinie berechnet."
            )
        self.canRunInBackground = True
        self.category = "Berechnungsnetz"

    def getParameterInfo(self):
        """Define parameter definitions for 'CreateVertices'.
         
        @param param0 in_cross_sections(DEFeatureClass):
            The input cross sections feature class. The parameter is 
            filtered to 'Polyline'.
        @param param1 in_wlb(DEFeatureClass):
            The input water land border feature class. The parameter is 
            filtered to 'Polyline'.
        @param param2 in_tin(DETin):
            The input triangulated irregular network.
        @param param3 workspace(DEWorkspace):
            Workspace for results. The parameter is filtered to 'Local
            Database'.
        @param param4 out_cross_lines_name(GPString):
            The name of the feature class with the cross lines.
        @param param5 out_vertices_name(GPString):
            The name of the feature class with the vertices.
        @param param6 element_count_method(GPString):
            The element count method. The default value is 'FIX'. The
            parameter is filtered to 'FIX' and 'VARIABLE'.
        @param param7 remain_percentage(GPLong):
            The percentage value between the current cross line and the 
            cross section at the end which must be reached at least to
            create a further cross line at the half distance (The half 
            distance between the last cross line and the cross section
            at the end). The parameter is filtered to '30', '40' and 
            '50'. The default value is '50'.
        @param param8 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
         
        """ 
        param0 = arcpy.Parameter(
            displayName="Querprofile (In cross sections)",
            name="in_cross_sections",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param0.filter.list = ["Polyline"]
        
        param1 = arcpy.Parameter(
            displayName="WLG /Uferlinien (In water land border)",
            name="in_wlb",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param1.filter.list = ["Polyline"]
        
        param2 = arcpy.Parameter(
            displayName="TIN (In triangulated irregular network)",
            name="in_tin",
            datatype="DETin",
            parameterType="Required",
            direction="Input"
            )
        
        param3 = arcpy.Parameter(
            displayName="Ausgabe-Geodatabase (Workspace)",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
            )
        param3.filter.list = ["Local Database"]
        
        param4 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der St\xfctzlinien (Out cross "
                "lines name)"
                ),
            name="out_cross_lines_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param5 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der St\xfctzpunkte (Out "
                "vertices name)"
                ),
            name="out_vertices_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param6 = arcpy.Parameter(
            displayName=(
                "Verfahren zur Bestimmung der Elementanzahl pro Linie "
                "(Element count method)"
                ),
            name="element_count_method",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        param6.value = "FIX"
        param6.filter.type = "ValueList"
        param6.filter.list = ["FIX", "VARIABLE"]
        
        param7 = arcpy.Parameter(
            displayName=(
                "Prozentwert, bis zu dem eine weitere St\xfctzlinie auf "
                "halber Restdistanz erzeugt werden soll (Remain_percentage)"
                ),
            name="remain_percentage",
            datatype="GPLong",
            parameterType="Required",
            direction="Input"
            )
        param7.value = 50
        param7.filter.type = "ValueList"
        param7.filter.list = [30, 40, 50]
        
        param8 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param8.value = True
         
        params = [
            param0, param1, param2, param3, param4, param5, param6, param7,
            param8
            ]
        return params

    def isLicensed(self):
        """Allow the tool to execute, only if the 'ArcGIS for Desktop
        Advanced' license and the extension 'ArcGIS 3D Analyst' are 
        available.
        
        """
        try:
            if (arcpy.CheckProduct("arcinfo") != "AlreadyInitialized"
                    and arcpy.CheckProduct("arcinfo") != "Available"):
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("ArcGIS for Desktop Advanced license is unavailable.")
            return False
        try:
            if arcpy.CheckExtension("3D") != "Available":
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("Extension '3D Analyst' is unavailable.")
            return False

        return True  
    
    def updateMessages(self, parameters):
        """Modify the messages created by internal parameter validation.
        
        This method is called after internal validation.
        
        """
        if (parameters[6].value and parameters[6].hasError()):
            parameters[6].setErrorMessage(
                "Zul\xe4ssige Werte: 'FIX', 'VARIABLE'."
                ) 
        
        if (parameters[7].value and parameters[7].hasError()):
            parameters[7].setErrorMessage(
                "Zul\xe4ssige Werte: '30', '40', '50'."
                )  

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. Then the 
        function create_cross_lines is called and executed to create the
        cross lines on which the vertices are placed. Afterwards the 
        direction is checked and if necessary corrected. Finally the 
        function create_vertices is called and executed.
        
        """
        in_cross_sections = parameters[0].valueAsText
        in_wlb = parameters[1].valueAsText
        in_tin = parameters[2].valueAsText
        workspace = parameters[3].valueAsText
        out_cross_lines_name = parameters[4].valueAsText
        out_vertices_name = parameters[5].valueAsText
        element_count_method = parameters[6].valueAsText
        remain_percentage = parameters[7].value
        overwrite_output = parameters[8].value
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        logger.info("Start function create_cross_lines.")
        distance = ""
        cross_lines = create_cross_lines(
            workspace, in_cross_sections, in_wlb, distance,
            out_cross_lines_name, element_count_method, remain_percentage
            )
        logger.info("Create_cross_lines finished successfully.")
        
        logger.info(
            "Start function flip_line_direction to check and correct cross "
            "lines."
            )
        keep_names = True
        reference_where_clause = "WLBID = 1"
        out_features_name = ""
        cross_lines = flip_line_direction(
            workspace, cross_lines, in_wlb, out_features_name, keep_names,
            reference_where_clause
            )
        logger.info("Cross lines checked and flipped successfully.")
    
        logger.info("Start function create_vertices.")
        create_vertices(
            workspace, cross_lines, in_cross_sections, in_tin, 
            out_vertices_name, element_count_method
            )
        logger.info("Create_vertices finished successfully.")
        
    
        return
    
    
class CreateChannelMeshElements(object):
    """Tool that creates the elements for the channel mesh.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'CreateChannelMeshElements'."""
        self.label = "Erstelle Netzelemente"
        self.description = (
            "Erstellt die Elemente f\xfcr das Berechnungsnetz. Die Elemente "
            "bestehen aus Dreiecken und Vierecken, wobei Dreiecke nur dann "
            "f\xfcr den \xfcbergang zwischen zwei aufeinander folgenden"
            "Netzreihen (quer zur Flie\xdfrichtung) verwendet werden, wenn "
            "die Elementanzahl nicht identisch ist."
            )
        self.canRunInBackground = True
        self.category = "Berechnungsnetz"

    def getParameterInfo(self):
        """Define parameter definitions for 'CreateChannelMeshElements'.
         
        @param param0 in_vertices(DEFeatureClass):
            The input vertices feature class. The parameter is filterd
            to 'Point'.
        @param param1 workspace(DEWorkspace):
            Workspace for results. The parameter is filtered to 'Local
            Database'.
        @param param2 out_channel_mesh_elements_name(GPString):
            The name of the feature class with the channel mesh 
            elements.
        @param param3 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
         
        """ 
        param0 = arcpy.Parameter(
            displayName="Stuetzpunkte (In vertices)",
            name="in_vertices",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param0.filter.list = ["Point"]
        
        param1 = arcpy.Parameter(
            displayName="Ausgabe-Geodatabase (Workspace)",
            name="workspace",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
            )
        param1.filter.list = ["Local Database"]
        
        param2 = arcpy.Parameter(
            displayName=(
                "Name der Ausgabe-Feature-Class der Netzelemente (Out channel "
                "mesh elements name)"
                ),
            name="out_channel_mesh_elements_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param3 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param3.value = True
         
        params = [param0, param1, param2, param3]
        return params

    def isLicensed(self):
        """Allow the tool to execute, only if the 'ArcGIS for Desktop
        Advanced' license and the extension 'ArcGIS 3D Analyst' are 
        available.
        
        """
        try:
            if (arcpy.CheckProduct("arcinfo") != "AlreadyInitialized"
                    and arcpy.CheckProduct("arcinfo") != "Available"):
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("ArcGIS for Desktop Advanced license is unavailable.")
            return False
        try:
            if arcpy.CheckExtension("3D") != "Available":
                raise arcpy.ExecuteError
        except arcpy.ExecuteError:
            logger.error("Extension '3D Analyst' is unavailable.")
            return False

        return True    

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        First, the overwriteOutput settings are adjusted. Then the 
        function create_channel_mesh_elements is called and executed.
        
        """
        in_vertices = parameters[0].valueAsText
        workspace = parameters[1].valueAsText
        out_channel_mesh_elements_name = parameters[2].valueAsText
        overwrite_output = parameters[3].value
        
        logger.info("Start function overwrite_output_settings.")
        overwrite_output_settings(overwrite_output)
        logger.info("Overwrite_output_settings finished successfully.")
        
        logger.info("Start function create_channel_mesh_elements.")
        create_channel_mesh_elements(
            workspace, in_vertices, out_channel_mesh_elements_name
            )
        logger.info("Create_channel_mesh_elements finished successfully.")
    
        return
    
class CheckChannelMeshElements(object):
    """Tool that checks the element area and angle sizes.
    
    The functions and parameter are explained below.
    
    """
    def __init__(self):
        """Define the tool 'CheckChannelMeshElements'."""
        self.label = "Pr\xfcfe Netzelemente"
        self.description = (
            "Pr\xfcft die Fl\xe4chen- und Winkelgr\xf6\xdfen jedes Elements "
            "darauf, ob die angegebenen minimalen und maximalen Gr\xf6\xdfen "
            "\xfcber- oder unterschritten wurden. Die betreffenden Elemente "
            "werden in eine Textdatei geschrieben."
            )
        self.canRunInBackground = True
        self.category = "Berechnungsnetz"

    def getParameterInfo(self):
        """Define parameter definitions for 'CreateChannelMeshElements'.
         
        @param param0 in_channel_mesh_elements(DEFeatureClass):
            The input channel mesh elements feature class. The
            parameter is filtered to 'Polygon'.
        @param param1 check_angles(DEBoolean):
            Check the angle sizes. The default value is 'True'.
        @param param2 check_areas(DEBoolean):
            Check the area sizes. The default value is 'True'.
        @param param3 minimum_angle(GPLong):
            The minimum angle size. The default value is '20' degrees. 
            The parameter range is filtered to the values '20' degrees,
            '25' degrees and '30' degrees.
        @param param4 maximum_angle(GPLong):
            The maximum angle size. The default value is '130' degrees. 
            The parameter range is filtered to the values '110' degrees,
            '115' degrees, '120' degrees, '125' degrees and '130' 
            degrees.
        @param param5 area_factor(GPLong):
            The area factor. The default value is '2'. The parameter 
            range is filtered from '2' to '5'.
        @param param6 out_directory(DEFolder):
            Directory which will contain the output file.
        @param param7 out_file_name(GPString): 
            Name of the output file. 
        @param param8 overwrite_output(GPBoolean):
            Overwrite output? The default value is 'True'.
         
        """ 
        param0 = arcpy.Parameter(
            displayName="Netzelemente (In channel mesh elements)",
            name="in_channel_mesh_elements",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input"
            )
        param0.filter.list = ["Polygon"]
        
        param1 = arcpy.Parameter(
            displayName="Winkel ueberpr\xfcfen? (Check angles?)",
            name="check_angles",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param1.value = True
        
        param2 = arcpy.Parameter(
            displayName="Fl\xe4chen \xfcberpr\xfcfen? (Check areas?)",
            name="check_areas",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param2.value = True
        
        param3 = arcpy.Parameter(
            displayName="Minimaler Winkel [Grad] (Minimum angle [degrees])",
            name="minimum_angle",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input"
            )
        param3.value = 20
        param3.filter.type = "ValueList"
        param3.filter.list = [20, 25, 30]
        
        param4 = arcpy.Parameter(
            displayName="Maximaler Winkel [Grad] (Maximum angle [degrees])",
            name="maximum_angle",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input"
            )
        param4.value = 130
        param4.filter.type = "ValueList"
        param4.filter.list = [110, 115, 120, 125, 130]
        
        param5 = arcpy.Parameter(
            displayName=(
                "Faktor f\xfcr die Fl\xe4chen\xfcberpr\xfcfung (Area factor)"
                ),
            name="area_factor",
            datatype="GPLong",
            parameterType="Optional",
            direction="Input"
            )
        param5.value = 2
        param5.filter.type = "Range"
        param5.filter.list = [2, 5]
        
        param6 = arcpy.Parameter(
            displayName="Ausgabeverzeichnis (Out directory)",
            name="out_directory",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input",
            )
                    
        param7 = arcpy.Parameter(
            displayName="Name der Datei mit den Warnmeldungen (Out file name)",
            name="out_file_name",
            datatype="GPString",
            parameterType="Required",
            direction="Input"
            )
        
        param8 = arcpy.Parameter(
            displayName=(
                "Vorhandene Daten \xfcberschreiben? (Overwrite output?)"
                ),
            name="overwrite_output",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input"
            )
        param8.value = True
         
        params = [
            param0, param1, param2, param3, param4, param5, param6, param7,
            param8
            ]
        return params

    def isLicensed(self):
        """Allow the tool to execute always."""
        return True    
    
    def updateParameters(self, parameters):
        """Modify the values, properties and display of parameters.
        
        This method is called whenever a parameter has been changed.
        
        """
        if parameters[1].value:
            parameters[3].enabled = True
            parameters[4].enabled = True
        else:
            parameters[3].enabled = False
            parameters[4].enabled = False
        
        if parameters[2].value:
            parameters[5].enabled = True
        else:
            parameters[5].enabled = False
        
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal parameter validation.
        
        This method is called after internal validation.
        
        """
        if (not parameters[1].value and not parameters[2].value):
            parameters[1].setErrorMessage(
                "Keine \xfcberpr\xfcfung ausgew\xe4hlt."
                )
            parameters[2].setErrorMessage(
                "Keine \xfcberpr\xfcfung ausgew\xe4hlt."
                )
            
        if parameters[1].value:
            if not parameters[3].value:
                parameters[3].setErrorMessage("Eingabewert erforderlich.")
            if not parameters[4].value:
                parameters[4].setErrorMessage("Eingabewert erforderlich.")
                
        if (parameters[1].value and not parameters[5].value):
            parameters[5].setErrorMessage("Eingabewert erforderlich.")
            
        if (parameters[3].value and parameters[3].hasError()):
            parameters[3].setErrorMessage(
                "Zul\xe4ssige Werte: '20', '25' oder '30'."
                )
            
        if (parameters[4].value and parameters[4].hasError()):
            parameters[4].setErrorMessage(
                "Zul\xe4ssige Werte: '110', '115', '120', '125' oder '130'."
                )
            
        if (parameters[5].value and parameters[5].hasError()):
            parameters[5].setErrorMessage(
                "Zul\xe4ssige Werte: '2', '3', '4' oder '5'."
                )

    def execute(self, parameters, messages):
        """The source code of the tool.
        
        The parameters are defined in getParameterInfo.
        
        The function check_channel_mesh_elements is called and executed.
        
        """
        in_channel_mesh_elements = parameters[0].valueAsText
        check_angles = parameters[1].value
        check_areas = parameters[2].value
        minimum_angle = parameters[3].value
        maximum_angle = parameters[4].value
        area_factor = parameters[5].value
        out_directory = parameters[6].valueAsText
        out_file_name = parameters[7].valueAsText
        overwrite_output = parameters[8].value
        
        logger.info("Start function check_channel_mesh_elements.")
        check_channel_mesh_elements(
            in_channel_mesh_elements, check_angles, check_areas, minimum_angle,
            maximum_angle, area_factor, out_directory, out_file_name,
            overwrite_output
            )
        logger.info("Check_channel_mesh_elements finished successfully.")
    
        return