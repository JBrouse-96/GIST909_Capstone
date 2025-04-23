# -*- coding: utf-8 -*-

import arcpy
import arcpy.management
from arcpy.sa import *
import os
import shutil
import time
import webbrowser
import zipfile

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Captsone Tool"
        self.alias = "BCIS_Customs"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]

class Tool:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "LASD Retrieval and Viewshed"
        self.description = "Tool description goes here"

    def getParameterInfo(self):
        """Define the tool parameters."""

        # # Observer Location Input
        param0 = arcpy.Parameter(
            displayName="Observer Location Layer",
            name="Observer_Location_Layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        
        # Observer Location ID from SQL
        param1 = arcpy.Parameter(
            displayName="Observer Location ID",
            name="Observer_Location_ID",
            datatype="GPSQLExpression",
            parameterType="Required",
            direction="Input")
        param1.parameterDependencies = [param0.name]

        # Target Location Input
        param2 = arcpy.Parameter(
            displayName="Target Location Layer",
            name="Target_Location_Layer",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")
        
        # Target Location Input from SQL
        param3 = arcpy.Parameter(
            displayName="Target Location ID",
            name="Target_Location_ID",
            datatype="GPSQLExpression",
            parameterType="Required",
            direction="Input")
        param3.parameterDependencies = [param2.name]

        # Observer Offset in US Survey Feet
        param4_int = arcpy.Parameter(
            displayName="Observer Offset (AGL)",
            name="Observer_Offset",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")
        param4_int.value = "0 FeetUS"

        # Radius of buffer around proposed tower site
        param5 = arcpy.Parameter(
            displayName="Study Area Buffer Size",
            name="Study_Area_Buffer_Size",
            datatype="GPLinearUnit",
            parameterType="Required",
            direction="Input")
        param5.value = "0 MilesInt"

        #Derived output as a result of creating the Location Link line
        param6 = arcpy.Parameter(
            displayName="Location_Link",
            name="Location_Link",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output")
        
        # Derived output as a result of the Buffer Tool for Target Site
        param7 = arcpy.Parameter(
            displayName="Study Area Buffer",
            name="Study_Area_Buffer",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output")
        
        # Derived output as a result of the Merge Features Tool
        param8 = arcpy.Parameter(
            displayName="Conical Polygon",
            name="Conical_Polygon",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output")
        
        # URL to REST endpoint of PAMap dataset
        param9 = arcpy.Parameter(
            displayName="LAS Tile Layer REST URL",
            name="LAS_Tile_Layer_REST_URL",
            datatype="GPString",
            parameterType="Required",
            direction="Input")

        # Column name containing LAS Download Links
        param10 = arcpy.Parameter(
            displayName="Column Containing URL to LAS Dataset",
            name="LAS_Download_URL",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        
        # Derived output as a result of importing the tile layer
        param11 = arcpy.Parameter(
            displayName="LAS Tile Import",
            name="LAS_Tile_Import",
            datatype="GPString",
            parameterType="Derived",
            direction="Output")
        
        # Derived output as a result of the Copy Features tool
        param12 = arcpy.Parameter(
            displayName="LAS Tile Copy",
            name="LAS_Tile_Copy",
            datatype="DEFeatureClass",
            parameterType="Derived",
            direction="Output")
        
        # URL to folder where the LAS Data will be unzipped
        param13 = arcpy.Parameter(
            displayName="LAS Storage Folder",
            name="LAS_Storage_Folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input")
        param13.value = arcpy.mp.ArcGISProject('CURRENT').homeFolder+"\LiDAR"
        
        # Desired name of the out LAS dataset from the Create LAS Dataset tool
        param14 = arcpy.Parameter(
            displayName="LAS Out Dataset Name",
            name="LAS_Out_Dataset_Name",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param14.value = "LocationName_DatasetName_Year_LASDataset"
        
        # Derived output as a result of the Create LAS Dataset tool
        param15 = arcpy.Parameter(
            displayName="Create LAS Dataset",
            name="Create_LAS_Dataset",
            datatype="DELasDataset",
            parameterType="Derived",
            direction="Output")
        
        # Derived output as a result of the Create LAS Dataset Statistics tool
        param16 = arcpy.Parameter(
            displayName="Generate LAS Dataset Statistics",
            name="Generate_LAS_Dataset_Statistics",
            datatype="DEFile",
            parameterType="Derived",
            direction="Output")
        
        # Derived output as a result of the LAS Dataset to Raster tool
        param17 = arcpy.Parameter(
            displayName="LAS Dataset to Raster",
            name="LAS_Dataset_to_Raster",
            datatype="GPRasterDataLayer",
            parameterType="Derived",
            direction="Output")
        
        # Derived output as a result of the Geodesic Viewshed tool
        param18 = arcpy.Parameter(
            displayName="Geodesic Viewshed",
            name="Geodesic_Viewshed",
            datatype="GPRasterLayer",
            parameterType="Derived",
            direction="Output")
        
        # Boolean checkbox to rerun tool after LAS dataset has been filtered for errors
        param19 = arcpy.Parameter(
            displayName="Rerun",
            name="Rerun_tool",
            datatype="GPBoolean",
            parameterType="Optional",
            direction="Input")
        param19.value = "false"
        
        # Additional Variables
        params = [param0, param1, param2, param3, param4_int, param5, param6, param7, param8, param9, param10, param11, param12, param13, param14, param15, param16, param17, param18, param19]
        return params

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        # https://pro.arcgis.com/en/pro-app/latest/arcpy/functions/checkextension.htm

        try:
        # Check if Spatial Analyst extension is available
            if arcpy.CheckExtension("Spatial") == "Available":
                return True  # The tool can be run if Spatial Analyst is available
            else:
                pass
        except Exception:
            return False  # The tool cannot be run without Spatial Analyst

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        # Add a folder to store the LiDAR Data in the project's home folder.
        las_folder = arcpy.mp.ArcGISProject('CURRENT').homeFolder+"\LiDAR"
        if arcpy.Exists(las_folder):
            pass
        else:
            arcpy.management.CreateFolder(arcpy.mp.ArcGISProject('CURRENT').homeFolder, "LiDAR")
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        # Documentation
            # https://pro.arcgis.com/en/pro-app/latest/arcpy/get-started/describing-data.htm
            # https://www.geeksforgeeks.org/python-ways-to-initialize-list-with-alphabets/
            # https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/parameter.htm

        # Check the Observer Layer for the correct data type.
        if parameters[0].value:
            P0_describe = arcpy.Describe(parameters[0].value)
            if P0_describe.shapeType not in ('Point', 'multipoint'):
                parameters[0].setErrorMessage("000366: Invalid geometry type.")
                return
            else:
                parameters[0].clearMessage()
        
        # Check the Target Layer for the correct data type.
        if parameters[2].value:
            P2_describe = arcpy.Describe(parameters[2].value)  
            if P2_describe.shapeType not in ('Point', 'multipoint'):
                parameters[2].setErrorMessage("000366: Invalid geometry type.")
                return
            else:
                parameters[2].clearMessage()
        
        # Validate the output name for the param18 LAS Dataset.
        if parameters[14].value:
            #Check for naming errors at start of param14
            indx = [number for number in range(len(parameters[14].valueAsText))]
            lowercase = [letter for letter in [chr(i) for i in range(ord('a'), ord('z') + 1)]]
            uppercase = [letter for letter in [chr(i) for i in range(ord('A'), ord('Z') + 1)]]
            if parameters[14].valueAsText[0] in lowercase or parameters[14].valueAsText[0] in uppercase or parameters[14].valueAsText[0] is "_":
                pass
            else:
                parameters[14].setErrorMessage("000361: The name starts with an invalid character.")
                return
            for num in indx:
                if parameters[14].valueAsText[num] in lowercase or parameters[14].valueAsText[num] in uppercase or parameters[14].valueAsText[num] is "_" or parameters[14].valueAsText[num] in str([0,1,2,3,4,5,6,7,8,9]):
                    pass
                else:
                    parameters[14].setErrorMessage("000354: The name contains an invalid character.")
                    return
        return         

    def execute(self, parameters, messages):
        """The source code of the tool."""
        
        # Set Env Settings
        arcpy.env.workspace = 'CURRENT'
        aprx = arcpy.mp.ArcGISProject('CURRENT')
        map = aprx.activeMap
        gdb = aprx.defaultGeodatabase

        # Set the output coordinate system to the Maps if the User does not specify one in the tools ENV settings
        if arcpy.env.outputCoordinateSystem is None:
            arcpy.env.outputCoordinateSystem = map.spatialReference.factoryCode #3857
            arcpy.AddMessage(f"Output Coordinate System auto set to {arcpy.env.outputCoordinateSystem.name}")
        else:
            arcpy.AddMessage(f"Output Coordinate System is set to {arcpy.env.outputCoordinateSystem.name}")

        # GUI Core Parameters & Derived Outputs
        param0 = parameters[0].valueAsText # Observer Location Input
        param1 = parameters[1].valueAsText.split("= ")[1].replace("'","") # Observer Location ID from SQL
        param2 = parameters[2].valueAsText # Target Location Input
        param3 = parameters[3].valueAsText.split("= ")[1].replace("'","") # Target Location ID from SQL
        param4 = parameters[4].valueAsText # Observer Offset
        param5 = parameters[5].valueAsText # Radius of buffer around proposed tower site
        #param6 = Derived output as a result of creating the Location Link line
        #param7 = Derived output as a result of the Buffer Tool for Target Site
        #param8 = Derived output as a result of the Merge Features Tool
        param9 = parameters[9].valueAsText # URL to REST endpoint of PAMap dataset
        param10 = parameters[10].valueAsText # Column name containing LAS Download Links
        #param11 = Derived output as a result of importing the tile layer
        #param12 = Derived output as a result of the Copy Features tool
        param13 = parameters[13].valueAsText # URL to folder where the LAS Data will be unzipped
        param14 = parameters[14].valueAsText # Desired name of the out LAS dataset from the Create LAS Dataset tool
        #param15 = Derived output as a result of the Create LAS Dataset tool
        #param16 = Derived output as a result of the Create LAS Dataset Statistics tool
        #param17 = Derived output as a result of the LAS Dataset to Raster tool
        #param18 = Derived output as a result of the Geodesic Viewshed tool
        param19 = parameters[19].valueAsText # Boolean check indicating that portions of the script need rerun after filtering the bad data out of the LAS dataset

        # Pick values out of SQL statements
        param1_field = parameters[1].valueAsText.split("=")[0].replace(" ","") # Name of column from Observer Location SQL
        param3_field = parameters[3].valueAsText.split("=")[0].replace(" ","") # Name of column from Target Location SQL

        # Convert param4 to US Feet to match auto symbolization of end raster
        param4_int = str(float(param4.split(" ")[0]) * arcpy.LinearUnitConversionFactor(param4.split(" ")[1], "FeetUS")).replace(".", "_")
        
        if param19 == 'false':
            step1 = """
###################################
# Get XY of the observer location #
###################################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/latest/arcpy/data-access/searchcursor-class.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/get-started/reading-geometries.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/adderror.htm
            arcpy.AddMessage(step1)

            # Open a search cursor to access the shape geometry and specific field of the input dataset
            with arcpy.da.SearchCursor(param0, ["SHAPE@", param1_field]) as Observer_XY_cursor:
                for Observer_ID in Observer_XY_cursor:
                    # Set a boolean check variable to handle errors if the location name fails to be found
                    Observer_Found = False
                    # If the name of the record in the column param1_field matches the location name stored in param1:
                    if Observer_ID[1] == param1:
                        Observer_Found = True
                        if Observer_Found:
                            arcpy.AddMessage("Location "+Observer_ID[1]+ " found in input observer site locations layer.")
                            # Grab the XY geom of the Observer Site
                            for pnt in Observer_ID[0]:
                                Observer_XY = arcpy.Point(pnt.X, pnt.Y)
                                arcpy.AddMessage(f"Observer point coordinates aqcuired.")
                            break
                    # Otherwise if no match, move to the next record in the observer feature
                    else:
                        continue
                # Stop the script if no record in the observer feature matches the users input
                if Observer_Found == False:
                    arcpy.AddError("No matching Site IDs found. Verify Site ID and rerun tool.")
                    exit() 
            del Observer_XY_cursor
            step2="""
#################################
# Get XY of the target location #
#################################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/latest/arcpy/data-access/searchcursor-class.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/get-started/reading-geometries.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/adderror.htm
            arcpy.AddMessage(step2)

            # Open a search cursor to access the shape geometry and specific field of the input dataset
            with arcpy.da.SearchCursor(param2, ["SHAPE@", param3_field]) as Target_XY_cursor:
                for Target_ID in Target_XY_cursor:
                    # Set a boolean check variable to handle errors if the location name fails to be found
                    Target_Found = False
                    # If the name of the record in the column param3_field matches the location name stored in param3:
                    if str(Target_ID[1]) == param3:
                        Target_Found = True
                        if Target_Found:
                            arcpy.AddMessage("Location "+str(Target_ID[1])+ " found in input target locations layer.")
                            # Grab the XY geom of the Target Site
                            for pnt in Target_ID[0]:
                                Target_XY = arcpy.Point(pnt.X, pnt.Y)
                                arcpy.AddMessage(f"Target location coordinates aqcuired.")
                            break
                    # Otherwise if no match, move to the next record in the target feature
                    else:
                        continue
                # Stop the script if no record in the target feature matches the users input
                if Target_Found == False:
                    arcpy.AddError("No matching target location IDs found. Verify target location ID and rerun tool.")
                    exit() 
            del Target_XY_cursor

            step3= """
###########################################
# Generate line feature between locations #
###########################################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/exists.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/delete.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/create-feature-class.htm
                # https://pro.arcgis.com/en/pro-app/latest/arcpy/data-access/insertcursor-class.htm
                # https://pro.arcgis.com/en/pro-app/latest/arcpy/classes/polyline.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/mapping/map-class.htm
            arcpy.AddMessage(step3)

            # Check for existing features before continuing
            arcpy.AddMessage("Checking for existing Location_Link.")
            if arcpy.Exists(gdb+"\Location_Link"):
                arcpy.AddMessage("Existing Location_Link found. Deleting.")
                arcpy.management.Delete(gdb+"\Location_Link")
                arcpy.AddMessage(arcpy.GetMessages())
            else:
                arcpy.AddMessage("No existing Location_Link found. Generating fresh link.")

            # Create the new feature class to hold the polyline
            param6 = arcpy.management.CreateFeatureclass(gdb, "Location_Link", "POLYLINE", "", "", "", arcpy.env.outputCoordinateSystem, "", "", "", "", "", "")

            # Insert the point geometry coordinate pairs into the polylines geometry to form a polyline
            with arcpy.da.InsertCursor(param6, ["SHAPE@"]) as insert_cursor:
                # Create an array object with the point geometry coordinate pairs
                array = arcpy.Array([Observer_XY, Target_XY])
                # Convert the array into a polyline object
                line = arcpy.Polyline(array)
                # Insert the polyline into the new feature class
                insert_cursor.insertRow([line])

            map.addDataFromPath(param6)           
            step4="""
#################################################
# Generate study area buffer around Target site #
#################################################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/exists.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/delete.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/analysis/buffer.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/select-layer-by-attribute.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/mapping/map-class.htm
            arcpy.AddMessage(step4)

            # Check for existing features before continuing
            arcpy.AddMessage("Checking for an existing Site Buffer.")
            if arcpy.Exists(gdb+"\Site_Buffer"):
                arcpy.AddMessage("Existing Site Buffer found. Deleting.")
                arcpy.management.Delete(gdb+"\Site_Buffer")
                arcpy.AddMessage(arcpy.GetMessages())
            else:
                arcpy.AddMessage("No existing Site Buffer found. Generating fresh buffer.")

            arcpy.AddMessage("\nGenerating Site Buffer.")
            # Select the target feature that will be used for the buffer
            arcpy.management.SelectLayerByAttribute(param2, "NEW_SELECTION", f"{param3_field} = '{param3}'", "") 
            # Generate the buffer
            param7 = arcpy.analysis.Buffer(param2, "Site_Buffer", param5, "FULL", "ROUND", "ALL", "", "GEODESIC")
            # Clear the selection
            arcpy.management.SelectLayerByAttribute(param2, "CLEAR_SELECTION") 
            arcpy.AddMessage(arcpy.GetMessages())
            map.addDataFromPath(param7)

            step5="""
################################
# Generate the conical polygon #
################################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/exists.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/delete.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-statistics/linear-directional-mean.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/mapping/map-class.htm
                # https://pro.arcgis.com/en/pro-app/latest/arcpy/data-access/searchcursor-class.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/subdivide-polygon.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/select-layer-by-attribute.htm
                # https://pro.arcgis.com/en/pro-app/3.3/tool-reference/data-management/copy-features.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/delete-rows.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/create-feature-class.htm
                # https://pro.arcgis.com/en/pro-app/latest/arcpy/data-access/insertcursor-class.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/get-started/reading-geometries.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/select-layer-by-location.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/points-to-line.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/feature-to-polygon.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/analysis/pairwise-erase.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/merge.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/mapping/symbology-class.htm
                # https://pro.arcgis.com/en/pro-app/latest/arcpy/mapping/layer-class.htm
            arcpy.AddMessage(step5)

            # Check for existing features before continuing
            arcpy.AddMessage("Checking for existence of Location_Link_Directional_Mean.")
            if arcpy.Exists(gdb+"\Location_Link_Directional_Mean"):
                arcpy.AddMessage("Existing Location_Link_Directional_Mean found. Deleting.\n")
                arcpy.management.Delete(gdb+"\Location_Link_Directional_Mean")
                arcpy.AddMessage(arcpy.GetMessages())
            else:
                arcpy.AddMessage("No existing Location_Link_Directional_Mean found. Generating fresh directional mean.")
            # Compute the compass direction for Location_Link (param6)
            arcpy.stats.DirectionalMean(param6, gdb+"\Location_Link_Directional_Mean", "DIRECTION")
            map.addDataFromPath(gdb+"\Location_Link_Directional_Mean")

            # Add the compass bearing to a variable
            with arcpy.da.SearchCursor(gdb+"\Location_Link_Directional_Mean", "CompassA")as compass_cursor:
                for Directional_Mean in compass_cursor:
                    compass_bearing = Directional_Mean[0]

            # Check for existing features before continuing
            arcpy.AddMessage("\nChecking for existence of param7_Subdivide_Polygon.")
            if arcpy.Exists(gdb+"\param7_Subdivide_Polygon"):
                arcpy.AddMessage("Existing param7_Subdivide_Polygon found. Deleting.\n")
                arcpy.management.Delete(gdb+"\param7_Subdivide_Polygon")
                arcpy.AddMessage(arcpy.GetMessages())
            else:
                arcpy.AddMessage("No existing param7_Subdivide_Polygon found. Generating fresh directional mean.")
            # Create a copy of the target location buffer, then subdivide into three equal parts
            arcpy.management.SubdividePolygon(param7, "param7_Subdivide_Polygon", "NUMBER_OF_EQUAL_PARTS", 3, "", "", compass_bearing, "STRIPS")
            map.addDataFromPath(gdb+"\param7_Subdivide_Polygon")

            # Duplicate the subdivided polygon and delete the parts where the OID is greater than 1 
            arcpy.management.SelectLayerByAttribute(map.listLayers("param7_Subdivide_Polygon")[0], "NEW_SELECTION", "OBJECTID <> 1", "")
            arcpy.management.CopyFeatures(map.listLayers("param7_Subdivide_Polygon")[0], "param7_Subdivide_Polygon_OID1")
            map.addDataFromPath(gdb+"\param7_Subdivide_Polygon_OID1")
            arcpy.management.DeleteRows(map.listLayers("param7_Subdivide_Polygon")[0])

            # Create an empty feature class for converting the subdivided polygon vertices into points
            if arcpy.Exists(gdb+"\param7_Subdivide_Polygon_Vert2Pt"):
                arcpy.management.Delete(gdb+"\param7_Subdivide_Polygon_Vert2Pt")
            arcpy.management.CreateFeatureclass(gdb, "param7_Subdivide_Polygon_Vert2Pt", "POINT", "", "", "", arcpy.env.outputCoordinateSystem, "", "", "", "", "", "")

            # Grab the geometry coordinate pairs of the vertices and insert them into the empty feature class
            with arcpy.da.InsertCursor(gdb+"\param7_Subdivide_Polygon_Vert2Pt", ['SHAPE@XY']) as cursor:
                with arcpy.da.SearchCursor(map.listLayers("param7_Subdivide_Polygon")[0], ['SHAPE@']) as search_cursor:
                    for row in search_cursor:
                        polygon = row[0]
                        # Loop through the parts of the polygon by setting a range to get an index position
                        for part_index in range(polygon.partCount):
                            # Use the index position access a specific vertex
                            part = polygon.getPart(part_index)
                            # Iterate over vertices of each part
                            for vertex in part:
                                # Get the XY of the vertex
                                x, y = vertex.X, vertex.Y
                                # Create a point geometry from XY coordinates
                                point = arcpy.Point(x, y)
                                # Create a point feature and insert it into the output feature class
                                cursor.insertRow([point])
                del search_cursor
            del cursor
            map.addDataFromPath(gdb+"\param7_Subdivide_Polygon_Vert2Pt")

            # Select all vertex points that intersect with the duplicated subdivided polygon and then invert the selection to delete these points.
            arcpy.management.SelectLayerByLocation(map.listLayers("param7_Subdivide_Polygon_Vert2Pt")[0], "INTERSECT", map.listLayers("param7_Subdivide_Polygon_OID1")[0], "", "NEW_SELECTION", "INVERT")
            arcpy.management.DeleteRows(map.listLayers("param7_Subdivide_Polygon_Vert2Pt")[0])

            # Check for existing features before continuing
            # Select the Observer point to be included in the merge
            arcpy.management.SelectLayerByAttribute(param0, "NEW_SELECTION", f"{param1_field} = '{param1}'", "")
            arcpy.AddMessage("\nChecking for existence of param7_merged_points.")
            if arcpy.Exists(gdb+"\param7_merged_points"):
                arcpy.AddMessage("Existing param7_merged_points found. Deleting.")
                arcpy.management.Delete(gdb+"\param7_merged_points")
                arcpy.AddMessage(arcpy.GetMessages())
            else:
                arcpy.AddMessage("No existing param7_merged_points found. Generating fresh points.")
            # Create a new point feature class so the subdivided polygon vertice points can be merged with the observers point
            arcpy.management.Merge([gdb+"\param7_Subdivide_Polygon_Vert2Pt", param0], gdb + "\param7_merged_points")
            arcpy.AddMessage(arcpy.GetMessages())
            map.addDataFromPath(gdb + '\param7_merged_points')
            # Clear the selection on the observer point
            arcpy.SelectLayerByAttribute_management(param0,"CLEAR_SELECTION")

            # Check for existing features before continuing
            arcpy.AddMessage("\nChecking for existence of param7_merged_points_2_Line.")
            if arcpy.Exists(gdb+"\param7_merged_points_2_Line"):
                arcpy.AddMessage("Existing param7_merged_points_2_Line found. Deleting.")
                arcpy.management.Delete(gdb+"\param7_merged_points_2_Line")
                arcpy.AddMessage(arcpy.GetMessages())
            else:
                arcpy.AddMessage("No existing param7_merged_points_Line found. Generating fresh polygon.")
            # Convert the points to a closed line
            arcpy.management.PointsToLine(gdb + '\param7_merged_points', gdb+"\param7_merged_points_2_Line", "", "OBJECTID", "CLOSE")
            arcpy.AddMessage(arcpy.GetMessages())
            map.addDataFromPath(gdb + '\param7_merged_points_2_Line')

            # Check for existing features before continuing
            arcpy.AddMessage("\nChecking for existence of Triangle Polygon.")
            if arcpy.Exists(gdb+"\Triangle_Polygon"):
                arcpy.AddMessage("Existing Triangle Polygon found. Deleting.")
                arcpy.management.Delete(gdb+"\Triangle_Polygon")
                arcpy.AddMessage(arcpy.GetMessages())
            else:
                arcpy.AddMessage("No existing Triangle Polygon found. Generating fresh polygon.")
            # Convert the closed line to a polygon to form a triangle
            arcpy.management.FeatureToPolygon(gdb + '\param7_merged_points_2_line', "Triangle_Polygon")
            map.addDataFromPath(gdb+"\Triangle_Polygon")

            # Check for existing features before continuing
            arcpy.AddMessage("\nChecking for existence of Triangle Polygon Erase.")
            if arcpy.Exists(gdb+"\Triangle_Polygon_Erase"):
                arcpy.AddMessage("Existing Triangle Polygon Erase found. Deleting.")
                arcpy.management.Delete(gdb+"\Triangle_Polygon_Erase")
                arcpy.AddMessage(arcpy.GetMessages())
            else:
                arcpy.AddMessage("No existing Triangle Polygon found. Generating fresh polygon.")
            # Use the erase tool to remove parts of the triangle polygon overlapping the target buffer
            arcpy.analysis.PairwiseErase(gdb+"\Triangle_Polygon", param7, "Triangle_Polygon_Erase")
            map.addDataFromPath(gdb+"\Triangle_Polygon_Erase")

            # Check for existing features before continuing
            arcpy.AddMessage("\nChecking for existence of Conical Polygon.")
            if arcpy.Exists(gdb+"\Conical_Polygon"):
                arcpy.AddMessage("Existing Conical Polygon found. Deleting.")
                arcpy.management.Delete(gdb+"\Conical_Polygon")
                arcpy.AddMessage(arcpy.GetMessages())
            else:
                arcpy.AddMessage("No existing Conical Polygon. Generating fresh polygon.")
            # Merge the remaining portion of the erased polygon and target buffer to create the conical polygon
            param8 = arcpy.management.Merge([gdb+"\Triangle_Polygon_Erase", param7],"Conical_Polygon")
            map.addDataFromPath(gdb+"\Conical_Polygon")
            arcpy.AddMessage("\nAdjusting symbology settings for Conical Polygon.")

            # Access the symbology properties of Conical Polygon
            sym = map.listLayers("Conical_Polygon")[0].symbology

            # Set the symbology to red outline 2pt, transparent fill
            sym.renderer.symbol.applySymbolFromGallery("Black Outline (2 pts)")
            sym.renderer.symbol.color = {'RGB': [255, 0, 0, 0]}
            sym.renderer.symbol.outlineColor = {'CMYK': [0, 100, 100, 0, 100]}
            sym.renderer.symbol.size = 2

            # Save the updated symbology settings to the layer
            map.listLayers("Conical_Polygon")[0].symbology = sym
            arcpy.AddMessage("Conical polygon symbology updated.")

            step6="""
##################################
# Clean up geoprocessing outputs #
##################################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/delete.htm
            arcpy.AddMessage(step6)

            arcpy.AddMessage("Deleting Location Link Line.")
            arcpy.management.Delete(gdb+"\Location_Link")
            arcpy.AddMessage(arcpy.GetMessages())

            arcpy.AddMessage("\nDeleting Location Directinal Mean.")
            arcpy.management.Delete(gdb+"\Location_Link_Directional_Mean")
            arcpy.AddMessage(arcpy.GetMessages())

            arcpy.AddMessage("\nDeleting Site Buffer.")
            arcpy.management.Delete(gdb+"\Site_Buffer")
            arcpy.AddMessage(arcpy.GetMessages())

            arcpy.AddMessage("\nDeleting param 7 merged points.")
            arcpy.management.Delete(gdb+"\param7_merged_points")
            arcpy.AddMessage(arcpy.GetMessages())

            arcpy.AddMessage("\nDeleting param 7 merged points 2 line.")
            arcpy.management.Delete(gdb+"\param7_merged_points_2_Line")
            arcpy.AddMessage(arcpy.GetMessages())

            arcpy.AddMessage("\nDeleting param 7 subdivide polygon.")
            arcpy.management.Delete(gdb+"\param7_Subdivide_Polygon")
            arcpy.AddMessage(arcpy.GetMessages())

            arcpy.AddMessage("\nDeleting param 7 subdivide polygon OID2.")
            arcpy.management.Delete(gdb+"\param7_Subdivide_Polygon_OID1")
            arcpy.AddMessage(arcpy.GetMessages())

            arcpy.AddMessage("\nDeleting param 7 Subdivide Polygon vert 2 pt.")
            arcpy.management.Delete(gdb+"\param7_Subdivide_Polygon_Vert2Pt")
            arcpy.AddMessage(arcpy.GetMessages())

            arcpy.AddMessage("\nDeleting Triangle Polygon.")
            arcpy.management.Delete(gdb+"\Triangle_Polygon")
            arcpy.AddMessage(arcpy.GetMessages())

            arcpy.AddMessage("\nDeleting Triangle Polygon Erase.")
            arcpy.management.Delete(gdb+"\Triangle_Polygon_Erase")
            arcpy.AddMessage(arcpy.GetMessages())

            arcpy.AddMessage("\nGeoprocessing Outputs Cleaned Up.")

            step7="""
################################
# Import LiDAR grid from PAMap #
################################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/mapping/map-class.htm
            arcpy.AddMessage(step7)

            # Import the tile layer from the REST URL
            param11 = map.addDataFromPath(param9)
            if arcpy.Exists(param11.name):
                arcpy.AddMessage("LiDAR Grid Imported Successfully.")
            else:
                arcpy.AddMessage("LiDAR Grid Import unsuccessful.")

            step8="""
############################################
# Select tiles overlapping conical polygon #
############################################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/select-layer-by-location.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/exists.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/delete.htm
                # https://pro.arcgis.com/en/pro-app/3.3/tool-reference/data-management/copy-features.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/mapping/symbology-class.htm
                # https://pro.arcgis.com/en/pro-app/latest/arcpy/mapping/layer-class.htm
            arcpy.AddMessage(step8)

            # Select tiles that intersect with the conical polygon
            arcpy.management.SelectLayerByLocation(param11, "INTERSECT", param8, "", "NEW_SELECTION", "NOT_INVERT")
            
            # Check for existing features before continuing
            arcpy.AddMessage("Checking for existence of a copied LiDAR Grid.")
            if arcpy.Exists(gdb+"\Copy_of_LiDAR_Grid"):
                arcpy.AddMessage("Existing copied LiDAR Grid found. Deleting.")
                arcpy.management.Delete(gdb+"\Copy_of_LiDAR_Grid")
                arcpy.AddMessage(arcpy.GetMessages())
            else:
                arcpy.AddMessage("No existing copied LiDAR Grid found.")
            arcpy.AddMessage("\nGenerating fresh grid.")
            # Copy the selected tiles to a new feature
            param12 = arcpy.management.CopyFeatures(param11, gdb+"\Copy_of_LiDAR_Grid", "", "", "", "")
            # Remove the original tile layer
            arcpy.AddMessage("\nRemoving Original LiDAR Grid Layer.")
            arcpy.management.Delete(map.listLayers(param11.name)[0])
            arcpy.AddMessage(arcpy.GetMessages())

            map.addDataFromPath(param12)
            arcpy.AddMessage("\nAdjusting symbology settings for Copied LiDAR Grid.")

            # Access the symbology properties of the copied LiDAR Grid
            sym = map.listLayers(map.listLayers("Copy_of_LiDAR_Grid")[0])[0].symbology

            # Set symbology to red outline 2pt, transparent fill
            sym.renderer.symbol.applySymbolFromGallery("Black Outline")
            sym.renderer.symbol.color = {'RGB' : [255, 0, 0, 0]}
            sym.renderer.symbol.outlineColor = {'CMYK' : [0, 100, 100, 0, 100]}
            sym.renderer.symbol.size = 2

            # Save updated symbology settings to the layer
            map.listLayers(os.path.basename(param12.getOutput(0)))[0].symbology = sym
            arcpy.AddMessage("Symbology updated.")

            step9="""
#######################
# Download LiDAR data #
#######################
"""
            arcpy.AddMessage(step9)

            # Create a list to store download URLs
            LAS_Download_URLs = []
            # Create a list to store the file paths of the las files in the parma13 folder
            # This list allows the tool to select only the required las files from a storage folder if this folder is a central storage for las datasets
            param15_Input_URLs = []

            # Initialize a counter to track number of datasets that need to be downloaded
            count = 0
            # Use a search cursor to append the download URLs to a list, and increment the counter up
            with arcpy.da.SearchCursor(param12, param10) as LAS_Download:
                for row in LAS_Download:
                    # reformat the URLs if they're contained inside HTML
                    url = str(row[0]).replace('<a href="', "").replace('">Download</a>', "")
                    LAS_Download_URLs.append(url)
                    count = count + 1

            # Indicate the number of files needing to be downloaded
            arcpy.AddMessage("\n"+ str(count) + " files will be downloaded.")

            # Download each URL and save it to the specified directory
            arcpy.AddMessage("Files will be downloaded to C:\Downloads.\n")
            for url in LAS_Download_URLs:

                # Create variables that will dynamically change for each URL in the downloads URL list
                zip_file_name = os.path.basename(url) # 35001390PAS_SW_LAS.zip
                os_downloads_folder = os.path.expanduser("~\\Downloads") #C:\Users\User\Downloads
                Downloads_Folder_LAS_File_Path = os.path.join(os_downloads_folder, zip_file_name) #C:\Users\User\Downloads\FILE_NAME.zip
                Project_LAS_File_Path = os.path.join(param13, zip_file_name) #C:\Project_Folder\Param13_Folder\FILE_NAME.zip
                
                # Check the counters value and display the appropriate message
                if count == len(LAS_Download_URLs):
                    pass
                elif count == 1:
                    arcpy.AddMessage("\n"+ str(count) + " file remaining for download.")
                else:
                    arcpy.AddMessage("\n"+ str(count) + " files remaining for download.")
                
                # Check for the file in multiple folders, or download it.
                # Initialize a boolean check
                file_download = 'false'
                while True: # Sets an infinite loop until a break is executed

                    # Use inline list comprehension to check if the file is actively downloading
                    # This check needs be at the top of the loop incase a redownload is triggered by a missing .las within a zip file
                    active_download = [f for f in os.listdir(os_downloads_folder) if f.endswith(".crdownload") or f.endswith(".part") or f.endswith(".download")]
                    if active_download:
                        file_download = 'true'
                        arcpy.AddMessage(f"Waiting for {zip_file_name} to finish downloading...")
                        arcpy.AddMessage("Checking again in 5s..\n")
                        time.sleep(5)  # Wait a bit before checking again
                        continue
                    
                    # Check if the file exists in the project folder
                    if arcpy.Exists(Project_LAS_File_Path) and file_download == 'false':
                        arcpy.AddMessage("\n"+ zip_file_name +" already exists in project folder.")
                        # Read the contents of the zipped folder
                        arcpy.AddMessage("Verifying existance of .las file..")
                        # Initialize a boolean check
                        las_found = False
                        with zipfile.ZipFile(Project_LAS_File_Path, 'r') as zip_contents:
                            # Find the .las in the ZIP file
                            for file_name in zip_contents.namelist():
                                if file_name.endswith(".las"):
                                    las_found = True
                                    break
                            if las_found == True:
                                # Check if the .las is already unzipped
                                if arcpy.Exists(param13 + "\\" + file_name):
                                    # Add its path to a list if it exists
                                    param15_Input_URLs.append(param13 + "\\" + file_name)
                                    arcpy.AddMessage(file_name +" exists in project folder.")
                                    count -= 1 # Increment the counter down for the GUI message to print
                                    if count == 0:
                                        arcpy.AddMessage("Downloads Complete.\n")
                                        break
                                    else:
                                        arcpy.AddMessage("Checking for the next file.\n")
                                        break
                                else:
                                    # Unzip the .zip, then add the path to a list
                                    shutil.unpack_archive(Project_LAS_File_Path, param13)
                                    # Add its path to a list
                                    param15_Input_URLs.append(param13 + "\\" + file_name)
                                    count -= 1 # Increment the counter down for the GUI message to print
                                    if count == 0:
                                        arcpy.AddMessage("Downloads Complete.\n")
                                        break
                                    else:
                                        arcpy.AddMessage(f"{zip_file_name} unzipped. Checking for the next file.\n")
                                        break # Move to the next URL in the list
                            elif las_found == False:
                                # No las file could be found, initiate a download to replace it
                                arcpy.AddMessage(f"Warning: A .las file could not be found in {zip_file_name}. Redownloading dataset.")
                                zipfile.ZipFile.close(zip_contents)
                                # Delete the zip with the missing las file
                                arcpy.management.Delete(Project_LAS_File_Path)
                                webbrowser.open(url)
                                time.sleep(10) # Wait a bit before continuing the loops
                                break                             
                            else:
                                break      
                        zipfile.ZipFile.close(zip_contents)

                    # Check if the file exists in the downloads folder
                    elif arcpy.Exists(Downloads_Folder_LAS_File_Path):
                        arcpy.AddMessage(f"\n{zip_file_name} found in {os_downloads_folder}.")
                                
                        # Move the file to the param13 folder
                        shutil.move(Downloads_Folder_LAS_File_Path, param13)
                        arcpy.AddMessage(f"Moved {zip_file_name} to {param13}")

                        #unzip the file in the param13 folder
                        arcpy.AddMessage(f"Unzipping {zip_file_name}.")
                        shutil.unpack_archive(Project_LAS_File_Path, param13)
                        arcpy.AddMessage(f"{zip_file_name} unzipped.")

                        # Get the name of the LAS file in the zipped folder
                        with zipfile.ZipFile(Project_LAS_File_Path, 'r') as zip_contents:
                            # List the contents of the ZIP file
                            for file_name in zip_contents.namelist():
                                if file_name.endswith(".las"):
                                    #Append it to a list for later use
                                    param15_Input_URLs.append(param13 + "\\" + file_name)
                                    count -= 1 # Increment the counter down for the GUI message to print
                                    break

                        if count == 0:
                            arcpy.AddMessage("Downloads Complete.\n")
                        else:
                            arcpy.AddMessage("Checking for the next file.\n")
                        break # Move to the next URL in the list

                    # If nothing above triggers then initiate a download of the LAS dataset
                    else:
                        arcpy.AddMessage(f"\n{zip_file_name} not found in project or download folder. Downloading file.")
                        webbrowser.open(url)
                        time.sleep(10) # Wait a bit before continuing the loops
                        continue # Force the next cycle in the While True loop

            step10="""
######################
# Create LAS dataset #
######################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/exists.htm
                # https://pro.arcgis.com/en/pro-app/latest/arcpy/mapping/arcgisproject-class.htm # details aprx.homeFolder
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/delete.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/create-las-dataset.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/mapping/map-class.htm
            arcpy.AddMessage(step10)

            # Check for existing features before continuing
            arcpy.AddMessage("Checking for existing LAS Dataset.")
            if arcpy.Exists(aprx.homeFolder+"\\"+param14):
                arcpy.AddMessage("Existing LAS Dataset found. Deleting.")
                arcpy.management.Delete(aprx.homeFolder+"\\"+param14)
                arcpy.AddMessage(arcpy.GetMessages())
            else:
                arcpy.AddMessage("No existing copy of LAS Dataset found.")
            arcpy.AddMessage("\nGenerating fresh grid.")

            # Create the LAS Dataset from the las files
            param15 = arcpy.management.CreateLasDataset(param15_Input_URLs, param14, "NO_RECURSION", "", arcpy.env.outputCoordinateSystem, "", "", "", "", "", "")
            arcpy.AddMessage(arcpy.GetMessages())
            map.addDataFromPath(param15)
            cont = 'yes' # Tells the script to continue with executing the next blocks of code
        
        # Tells the script to start from here if the rerun parameter is true, or to continue if executing the full script
        if param19 == 'true' or cont == 'yes':
            step11="""
#################################
# Create LAS Dataset Statistics #
#################################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/exists.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/delete.htm
                # https://pro.arcgis.com/en/pro-app/3.3/tool-reference/data-management/las-dataset-statistics.htm
            arcpy.AddMessage(step11)

            # Check for existing features before continuing
            arcpy.AddMessage("Checking for existing LAS Dataset statistics.")
            if arcpy.Exists(aprx.homeFolder+"\\"+param14+"_statistics.csv"):
                arcpy.AddMessage("Existing LAS Dataset statistics found. Deleting.")
                arcpy.management.Delete(aprx.homeFolder+"\\"+param14+"_statistics.csv")
                arcpy.AddMessage(arcpy.GetMessages())
            else:
                arcpy.AddMessage("No existing LAS Dataset statistics found.")

            # Generate the dataset statistics.
            arcpy.AddMessage("\nGenerating fresh statistics. This may take a while.")
            param16 = arcpy.management.LasDatasetStatistics(map.listLayers(param14+".lasd")[0], "OVERWRITE_EXISTING_STATS", param14+"_statistics.csv", "DATASET", "SPACE", "DECIMAL_POINT")
            arcpy.AddMessage(arcpy.GetMessages())
            map.addDataFromPath(param16)

            step12="""
#################################
# Convert LAS Dataset to Raster #
#################################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/exists.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/delete.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/conversion/las-dataset-to-raster.htm
            arcpy.AddMessage(step12)

            # Check for existing features before continuing. Will overwrite previous rerun features if param19 is true
            if param19 == 'false':
                arcpy.AddMessage("Checking for existing LAS_Dataset_To_Raster.")
                if arcpy.Exists(gdb+"\LAS_Dataset_to_Raster"):
                    arcpy.AddMessage("Existing Raster found. Deleting.")
                    arcpy.management.Delete(gdb+"\LAS_Dataset_to_Raster")
                    arcpy.AddMessage(arcpy.GetMessages())
                else:
                    arcpy.AddMessage("No existing LAS_Dataset_To_Raster found.")
            else:
                arcpy.AddMessage("Checking for existing LAS_Dataset_To_Raster_rerun.")
                if arcpy.Exists(gdb+"\LAS_Dataset_to_Raster_rerun"):
                    arcpy.AddMessage("Existing Raster found. Deleting.")
                    arcpy.management.Delete(gdb+"\LAS_Dataset_to_Raster_rerun")
                    arcpy.AddMessage(arcpy.GetMessages())
                else:
                    arcpy.AddMessage("No existing LAS_Dataset_To_Raster_rerun found.")
            
            # Generate the Raster. Appends rerun to the name if param19 is true
            arcpy.AddMessage("\nGenerating fresh Raster. This may take a while.")
            if param19 == 'false':
                param17 = arcpy.conversion.LasDatasetToRaster(map.listLayers(param14+".lasd")[0], "LAS_Dataset_to_Raster", "ELEVATION", "BINNING MAXIMUM NONE", "FLOAT", "CELLSIZE", "10", "3.28")
            else:
                param17 = arcpy.conversion.LasDatasetToRaster(map.listLayers(param14+".lasd")[0], "LAS_Dataset_to_Raster_rerun", "ELEVATION", "BINNING MAXIMUM NONE", "FLOAT", "CELLSIZE", "10", "3.28")
                arcpy.AddMessage(arcpy.GetMessages())

            step13="""
##############################
# Generate Geodesic Viewshed #
##############################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/functions/exists.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/delete.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/data-management/select-layer-by-attribute.htm
                # https://pro.arcgis.com/en/pro-app/latest/tool-reference/spatial-analyst/viewshed-2.htm
                # https://pro.arcgis.com/en/pro-app/3.3/arcpy/mapping/map-class.htm
            arcpy.AddMessage(step13)

            # Check for existing features before continuing. Will overwrite previous rerun features if param19 is true
            if param19 == 'false':
                arcpy.AddMessage("Checking for existing Viewshed raster.")
                if arcpy.Exists(gdb+f"\Viewshed_{param1}_{str(param4_int)}agl"):
                    arcpy.AddMessage("Existing Viewshed raster found. Deleting.")
                    arcpy.management.Delete(gdb+f"\Viewshed_{param1}_{str(param4_int)}agl")
                    arcpy.AddMessage(arcpy.GetMessages())
                else:
                    arcpy.AddMessage("No existing Viewshed raster found.")
            
            else:
                arcpy.AddMessage("Checking for existing Viewshed raster.")
                if arcpy.Exists(gdb+f"\Viewshed_{param1}_{str(param4_int)}agl_rerun"):
                    arcpy.AddMessage("Existing Viewshed raster found. Deleting.")
                    arcpy.management.Delete(gdb+f"\Viewshed_{param1}_{str(param4_int)}agl_rerun")
                    arcpy.AddMessage(arcpy.GetMessages())
                else:
                    arcpy.AddMessage("No existing Viewshed raster found.")

            # Generate the viewshed. Appends rerun to the name if param19 is true
            arcpy.AddMessage("\nGenerating fresh Viewshed raster.")
            arcpy.management.SelectLayerByAttribute(param0, "NEW_SELECTION", parameters[1].valueAsText, "")
            if param19 == 'false':
                param18 = Viewshed2(gdb+"\LAS_Dataset_to_Raster", param0, f"Viewshed_{param1}_{str(param4_int)}agl", "FREQUENCY", "0 Meters", None, 0.13, "0 Meters", None, f"{param4}", None, "GROUND", None, "GROUND", 0, 360, 90, -90, "ALL_SIGHTLINES", "GPU_THEN_CPU")
                map.addDataFromPath(gdb+f"\Viewshed_{param1}_{str(param4_int)}agl")
            else:
                param18 = Viewshed2(gdb+"\LAS_Dataset_to_Raster_rerun", param0, f"Viewshed_{param1}_{str(param4_int)}agl_rerun", "FREQUENCY", "0 Meters", None, 0.13, "0 Meters", None, f"{param4}", None, "GROUND", None, "GROUND", 0, 360, 90, -90, "ALL_SIGHTLINES", "GPU_THEN_CPU")
                map.addDataFromPath(gdb+f"\Viewshed_{param1}_{str(param4_int)}agl_rerun")

            arcpy.AddMessage(arcpy.GetMessages())
            arcpy.SelectLayerByAttribute_management(param0,"CLEAR_SELECTION")

            step14="""
#######################################
# Change Symobology of Viewshed Layer #
#######################################
"""
            # ESRI Reference documentation for this step:
                # https://pro.arcgis.com/en/pro-app/latest/arcpy/mapping/rasterclassifycolorizer-class.htm
                # https://pro.arcgis.com/en/pro-app/latest/arcpy/mapping/layer-class.htm
            arcpy.AddMessage(step14)

            # Acccess the symbology settings of the viewshed layer via the contents. Dependent on param19 value
            if param19 == 'false':
                sym = map.listLayers(f"Viewshed_{param1}_{str(param4_int)}agl")[0].symbology
            else:
                sym = map.listLayers(f"Viewshed_{param1}_{str(param4_int)}agl_rerun")[0].symbology

            sym.colorizer.classificationField = ""
            sym.colorizer.breakCount = 3
            sym.colorizer.noDataColor = {'RGB': [255, 255, 255, 0]}

            # Set the intial break values for the symbology outside of the loop. Dependent on param19 value
            breakVal = 80
            if param19 == 'false':
                max_val = arcpy.GetRasterProperties_management(map.listLayers(f"Viewshed_{param1}_{str(param4_int)}agl")[0], "MAXIMUM")
            else:
                max_val = arcpy.GetRasterProperties_management(map.listLayers(f"Viewshed_{param1}_{str(param4_int)}agl_rerun")[0], "MAXIMUM")

            # Adjust the breaks
            for brk in sym.colorizer.classBreaks:
                if breakVal == 80:
                    brk.upperBound = breakVal
                    brk.label = "AGL up to 80ft"
                    brk.description = "0 - 80"
                    brk.color = {'RGB' : [76, 230, 0, 40]}
                    breakVal =120
                elif breakVal == 120:
                    brk.upperBound = breakVal
                    brk.label = "AGL greater than 80ft"
                    brk.description = "80.1 - 120"
                    brk.color = {'RGB' : [0, 197, 255, 40]}
                    breakVal = max_val.getOutput(0)
                elif breakVal == max_val.getOutput(0):
                    brk.upperBound = float(breakVal)
                    brk.label = "AGL greater than 120ft"
                    brk.description = "120.1 - {}".format(float(max_val.getOutput(0)))
                    brk.color = {'RGB' : [0, 0, 0, 0]}

            # Apply the symbology settings. Dependent on param19 value
            if param19 == 'false':
                map.listLayers(f"Viewshed_{param1}_{str(param4_int)}agl")[0].symbology = sym
            else:
                map.listLayers(f"Viewshed_{param1}_{str(param4_int)}agl_rerun")[0].symbology = sym
            arcpy.AddMessage("Default Symbology applied. Adjust as needed.")
            aprx.save

            step14="""
#######################################
# Script Executed. Verify Results and #
# use the rerun option if needed      #
#######################################
"""
            arcpy.AddMessage(step14)
            return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return