"""
@name:          Make3d
@description:   extrudes curves for TheNewMakers milling template
@author:        tim castelijn
@version:       0.6
@link:          https://github.com/timcastelijn/rhinoscript
@notes:         Works with Rhino 5.

"""

# V0.0.1

# to install as command (alias) or keyboard shortcut, use line below and change to your script file path

# '_-runPythonScript "E:/rhinoscript/make3d.py"


import sys
import os

print os.path.dirname(__file__) + "\..\checkAndExport"
sys.path.insert(0, os.path.dirname(__file__) + "\..\checkAndExport")

import rhinoscriptsyntax as rs
import Rhino
import math
import re
import time
import scriptcontext
import checkAndExport as ce

# SCRIPT GLOBALS
EXPORT_FONT = 'timfont'
MAT_THICKNESS = 18

#add to rhino as an alias
if not rs.IsAlias("TNM_make3d"):
    rs.AddAlias("TNM_make3d",  "'_-runPythonScript \"%s\"" % __file__ )
    print 'addAlias'
else:
    print 'alias could not be added'

# recursive explode of blocks
def iterateBlocks(objects):

    def explode(objs, li):
        for obj in objs:
            if rs.IsBlockInstance(obj):

                # DIRTY FIX FOR RHINO 5-SR14 522.8390 (5-22-2017)
                # temp_objs = rs.ExplodeBlockInstance(obj)

                rs.UnselectAllObjects()
                rs.SelectObject(obj)
                rs.Command("Explode" , False)
                temp_objs = rs.LastCreatedObjects()

                explode(temp_objs, li)
            else:
                li.append(obj)

        return li

    #create empty list
    li = []

    #redeclare objects list with content of exploded blocks
    return explode(objects, li)


def simplify(objs):
    for obj in objs:
        if rs.IsCurve(obj):
            rs.SimplifyCurve(obj)

def createPockets(tool_id, operation, z_pos, obj):

    if operation == 'Inner contour' or operation == 'Pocket' or operation=='Drill':
        surface_id = rs.ExtrudeCurveStraight( obj, (0,0,0), (0, 0, MAT_THICKNESS+2) )
        rs.CapPlanarHoles(surface_id)
        rs.MoveObject(surface_id, (0,0,z_pos))
        
        return surface_id
        
def makeExtrusions(tool_id, operation, z_pos, obj, material_thickness):
    
    if operation == 'Outer contour':
        surface_id = rs.ExtrudeCurveStraight( obj, (0,0,0), (0, 0, material_thickness) )
        rs.CapPlanarHoles(surface_id)
        return surface_id        
        
def sweepVolume(crv, tool_id, z_pos):

    tangent = rs.CurveTangent(crv, rs.CurveParameter(crv, 0))
    origin = rs.CurveStartPoint(crv)
    
    block = rs.InsertBlock( 'T_' + tool_id, (0,0,0), scale=(1,1,1) )
    

    # rs.DeleteObjects(objs)
       
    # pt2 = [origin.X, origin.Y + perp.XAxis[1], origin.Z]
    pt2 = [origin.X, origin.Y , origin.Z + 1]
    pt3 = [origin.X + tangent.X, origin.Y + tangent.Y , origin.Z + tangent.Z]

    ref     = [(0,0,0),(0,1,0),(0,0,1)] 
    target  = [origin, pt2 ,pt3]
    
    
    block = rs.OrientObject(block, ref, target)
    
    objs = rs.ExplodeBlockInstance(block)
    profile = None
    for item in objs:
        if rs.ObjectLayer(item) == 'HULP::C_Toolcontours' or rs.ObjectLayer(item) == 'Hulp::C_Toolcontours':
            profile = rs.CopyObject(item)
            
    
    rs.DeleteObjects(objs)


    
    if not profile:
        rs.MessageBox('there is no layer named "C_Toolcontours" in block %s' % rs.BlockInstanceName(block))
        return False
            
    profile = rs.OffsetCurve(profile, rs.CurveAreaCentroid(profile)[0], 0.001, style=1)
    
    # rs.MoveObject(profile, (0,0,z_pos))
            
    
    # rail = obj
    # rail_crv = rs.coercecurve(rail)
    # if not rail_crv: return
    # 
    # cross_sections = [profile]
    # if not cross_sections: return
    # cross_sections = [rs.coercecurve(crv) for crv in cross_sections]
    # 
    # sweep = Rhino.Geometry.SweepOneRail()
    # sweep.AngleToleranceRadians = scriptcontext.doc.ModelAngleToleranceRadians
    # sweep.ClosedSweep = True
    # # sweep.MiterType  = 2
    # sweep.SweepTolerance = scriptcontext.doc.ModelAbsoluteTolerance
    # sweep.SetToRoadlikeTop()
    # breps = sweep.PerformSweep(rail_crv, cross_sections)
    # for brep in breps: scriptcontext.doc.Objects.AddBrep(brep)
    # scriptcontext.doc.Views.Redraw()
    # 
    # # surface_id = rs.LastCreatedObjects()

    
    # METHOD1
    surface_id = rs.AddSweep1( crv, profile, True )    

    rs.CapPlanarHoles(surface_id)
    
    pt = rs.CurveAreaCentroid(profile)[0]
    pt2 = (pt.X, pt.Y, pt.Z+1)
    
    rev = rs.AddRevSrf( profile, (pt, pt2) )
    

    rs.MoveObject(rev, (0,0,z_pos))  
    rs.MoveObject(surface_id, (0,0,z_pos)) 

    
    rs.CapPlanarHoles(surface_id)
    
    
    
    return [surface_id]        

    
    
    rs.UnselectAllObjects()
    rs.SelectObjects([crv, profile])
    
    result = rs.Command("_-Sweep1 _Enter Style=RoadlikeTop _Enter", False)
            
    if result: 
        rs.DeleteObject(profile)
        surface_id = rs.LastCreatedObjects()

        rs.CapPlanarHoles(surface_id)
    
        rs.DeleteObjects(objs)
        rs.MoveObject(surface_id, (0,0,z_pos))

        return surface_id        
        
def makeEngraves(tool_id, operation, z_pos, obj):

    #restore view cplane
    p1 = rs.WorldXYPlane()
    rs.ViewCPlane(None, p1)
            
    return sweepVolume(obj, tool_id, z_pos)
                 
def convertToVolumes( objs, material_thickness ):
    invalid_layers =[]
    
    # first find relevant layers
    layers = []
    volumes = []
    subtracts = []
    
    # sort objects
    for obj in objs:
        layer_name = rs.ObjectLayer(obj)
        
        m = ce.parseLayer(layer_name)

        if m and len(m.groups()) > 4:
            tool_id     = m.group(1)
            operation   = m.group(2)
            z_pos       = float(m.group(3) + m.group(4))
            
            if operation == 'Outer contour':
                volume = makeExtrusions(tool_id, operation, z_pos, obj, material_thickness)
                if volume:
                    volumes.append(volume) 
            elif operation == "Pocket" or operation == 'Pocket' or operation=='Drill' or operation == 'Inner contour':
                
                pocket =  createPockets(tool_id, operation, z_pos, obj)
                if pocket:
                    subtracts.append(pocket  )
                    
            elif operation == 'Engrave':
            
                engraves =  makeEngraves(tool_id, operation, z_pos, obj)
                for engrave in engraves:
                    subtracts.append(engrave ) 
        else:
            invalid_layers.append(layer_name)
        
    
    
    myset = set(invalid_layers)
    msg = 'layers could not be processed:\n'
    
    for layer in myset:
        msg += '- ' + layer + "\n"
    
    return volumes, subtracts
    

             
def addResultToBlock(obj, result):
             
            name = rs.BlockInstanceName(obj)
            i_point = rs.BlockInstanceInsertPoint(obj)
            xform = rs.BlockInstanceXform(obj)
            
            block_content = rs.ExplodeBlockInstance(obj)  

            bc=[]
            for c in block_content:
                bc.append(c)
            
            bc.append(result)
            
            rs.AddBlock(bc, i_point, name, True)
            
            rs.InsertBlock2(name, xform)     

def checkPos(objs):
    # if ok, start export
    copies = rs.CopyObjects( objs)
    copies = ce.explodeBlock( copies )
    
    # filter objects to only curves and points
    copies = ce.filterObjects(copies) 
    if not ce.checkCurvePosition(copies):
        rs.DeleteObjects(copies)    
        return False
        
    rs.DeleteObjects(copies)  


def storeDefaultValues(convert_for_biesse, export_clamex_txt):
    convert_for_biesse  = rs.SetDocumentData("CheckAndExport", "convert_for_biesse", str(convert_for_biesse))
    export_clamex_txt   = rs.SetDocumentData("CheckAndExport", "export_clamex_txt", str(export_clamex_txt))
    
        
def getDefaultValues(section, value):
    str_convert_for_biesse  = rs.GetDocumentData(section, "convert_for_biesse")
    str_export_clamex_txt   = rs.GetDocumentData("CheckAndExport", "export_clamex_txt")
    
    convert_for_biesse  = str_convert_for_biesse == 'True'
    export_clamex_txt   = str_export_clamex_txt == 'True'
    
    return (convert_for_biesse, export_clamex_txt)
        
    
    
# main script
def main():


    # get objects to export
    objs = rs.GetObjects("select objects to Make3d", 0, True, True)
    if not objs: print "make3d aborted"; return
    
    # default_thickness =  rs.GetDocumentData('TNM_make3d', 'material_thickness')
    # if default_thickness:
        # default_thickness = float( default_thickness )
    # else:
        # default_thickness = 18
    
    material_thickness = rs.GetReal("Material Thickness", number=18.3)

    # rs.SetDocumentData('TNM_make3d', 'material_thickness', str( material_thickness ) )
        
    
    rs.EnableRedraw(False)

    checkPos(objs)

    set_volumes = []
    set_subtracts = []
        
    for obj in objs:
        if rs.IsBlockInstance(obj):   
            
            # get content
            copy = rs.CopyObject(obj)
            content = ce.explodeBlock( [copy] )
            
            # filter objects to only curves and points
            copies = ce.filterObjects(content) 

            simplify(copies)

            volumes, subtracts = convertToVolumes(copies, material_thickness)
            
            
            part =  rs.BooleanDifference(volumes, subtracts)

            
            # addResultToBlock(obj, result)
            
        else:
            # add warning message collision check
            print obj
    
    rs.UnselectAllObjects()
    intersect = None
    # for i, volume in enumerate(set_volumes):
        # for j, subtracts in enumerate(set_subtracts):
            # if(i != j):
                # print rs.ObjectLayer(volume)
                
                # intersect = rs.BooleanIntersection(rs.CopyObject(volume), subtracts, False)
                # if intersect:
                    # rs.SelectObjects(intersect)
                    
                    
            # rs.DeleteObjects(subtracts)

            
       
    
    if intersect:
        rs.MessageBox("ERROR")

        
    ce.redraw()

    rs.DeleteObjects(copies)
                
            
if __name__ == "__main__":
    main();
