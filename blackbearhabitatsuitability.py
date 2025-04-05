# -*- coding: utf-8 -*-

import arcpy
from arcpy.sa import *

#Check for ArcGIS Spatial Analyst Extension
if arcpy.CheckExtension("Spatial") == "Available":
    arcpy.CheckOutExtension("Spatial")
else:
    arcpy.AddMessage("License not available")


class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = "toolbox"

        # List of tool classes associated with this toolbox
        self.tools = [BlackBearHabitatSuitability]


class BlackBearHabitatSuitability(object):
    def __init__(self):
        self.label = "Black Bear Suitability Analysis"
        self.description = "Input a DEM and Land Classification Raster to calculate suitability analysis of Black Bears"

    def getParameterInfo(self):
        """Define the tool parameters."""
        #dem raster
        dem = arcpy.Parameter(
            displayName ="Digital Elevation Model",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")
        
        #landcover raster
        landcover = arcpy.Parameter(
            displayName ="Land Cover Raster",
            name="landcover",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input")

        #output raster
        output_raster = arcpy.Parameter(
            displayName = "Output Raster",
            name="output_raster",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Output")
        
        return [dem, landcover, output_raster]

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        try:

            #Set workspace to default
            arcpy.env.workspace = arcpy.env.scratchWorkspace
            arcpy.env.overwriteOutput = True
        
            #Pass parameters into function
            landcover = parameters[1].valueAsText
            elevation_raster = parameters[0].valueAsText
            suitability_raster = parameters[2].valueAsText

            #Generate edges raster
            #Create output raster to store edges
            edge_raster = arcpy.Raster(landcover)
            input_raster_info = edge_raster.getRasterInfo()
            input_raster_info.setNoDataValues(20)
            output_raster = arcpy.Raster(input_raster_info)

            #Iterate through raster to generate edges using relative indexing
            rci = RasterCellIterator({'rasters':[edge_raster, output_raster]})
            for i, j in rci:
                count = 0
                for relindx in [-1,0,1]:
                    for relindy in [-1,0,1]:
                        if edge_raster[i+relindx, j+relindy] != edge_raster[i,j]:
                            count += 1
                output_raster[i,j] = count


            #Save output raster
            edges_raster = "edge_raster"
            output_raster.save(edges_raster)

            #Generate slope raster (degrees)from elevation raster
            slope_raster = arcpy.Raster(elevation_raster)
            slope_raster_degree = Slope(slope_raster, "DEGREE")
            slopes_raster = "slopes_raster"
            slope_raster_degree.save(slopes_raster)

            #Reclassify edges raster into suitability scale
            reclassify_edges_raster = Reclassify(edges_raster, "Value", RemapRange([[0, 0, 1], [6, 8, 1], [2, 2, 2], [1, 1, 1], [3, 4, 4]]))

            #Reclassify slope raster into suitability scale
            reclassify_slope_raster = Reclassify(slopes_raster, "Value", RemapRange([[0, 10, 4], [10, 20, 3], [20, 30, 2], [30, 90, 1]]))

            #Reclassify landcover raster into suitability scale
            reclassify_landcover = Reclassify(landcover, "Value", RemapValue([[1,4], [2,4], [5,4], [6,4], [8,4], [10,4], [11,3], [12,3], [13,2], [14,3], [15,3], [16,1], [17,1], [18,1], [19,1]]))
            
            #Create weighted overlay table
            woTable = WOTable([
                [reclassify_edges_raster, 50, "VALUE", RemapValue([[1,1], [2,2], [3,3], [4,4]])],
                [reclassify_slope_raster, 35, "VALUE", RemapValue([[1,1], [2,2], [3,3], [4,4]])],
                [reclassify_landcover, 15, "VALUE", RemapValue([[1,1], [2,2], [3,3], [4,4]])]], [1,4,1])

            #Save weighted overlay table to output parameter
            outWeightedOverlay = WeightedOverlay(woTable)
            outWeightedOverlay.save(suitability_raster)

        except Exception as e:
            arcpy.AddMessage(f"Error: {str(e)}")
                
            

            
                            

            

        
    
