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


import rhinoscriptsyntax as rs
import Rhino
import math
import re
import time
import scriptcontext

# SCRIPT GLOBALS
EXPORT_FONT = 'timfont'
MAT_THICKNESS = 18

def redraw():
    rs.EnableRedraw(True)
    rs.EnableRedraw(False)

# function to reverse a curve if the normal points downwards in Z-dir
# assumed is that only closed curves can have inside or outside
def setCurveDir(objs):
    rs.UnselectAllObjects()
    count = 0

    for obj in objs:
        if rs.IsCurve(obj) and rs.IsCurveClosed(obj):
        
            # 1 = CW, -1 = CCW, 0 = N/A
            # -1 if the curve's orientation is counter-clockwise
            # 0 if unable to compute the curve's orientation
            if rs.ClosedCurveOrientation(obj) == 0:
                rs.SelectObject(obj)
                rs.MessageBox( "Curve direction could not be determined")
                return False
            if rs.ClosedCurveOrientation(obj) == 1:
                rs.ReverseCurve(obj)
                count += 1
                rs.SelectObject(obj)                    

                # normal = rs.CurveNormal(obj)
                # if normal and normal[2] < 0:
                    # count += 1
                    # rs.ReverseCurve(obj)
                    # rs.SelectObject(obj)
    
    # redraw()

    # rs.MessageBox( "reversed curves  " + str(count) + " curves")
    return True

def isCurveOnCPlane(obj):
    if rs.IsCurvePlanar(obj):
        data = rs.CurvePoints(obj)
        for pt in data:
            if(math.fabs( pt.Z )< 1e-8 ):
                return True

	return False

def isCurveBelowCPlane(obj):
    data = rs.CurvePoints(obj)
    for pt in data:
        if (pt.Z < -1e-8 ):
            return True

	return False

# append objectlayer to list
def appendLayer(layers, obj):
    layer = rs.ObjectLayer(obj)
    try:
        layers.index(layer)
        pass
    except Exception as e:
        layers.append( rs.ObjectLayer(obj) )

def projectLayersToClpane(layers):
    for layer in layers:
        curves = rs.ObjectsByLayer(layer)

        xform = rs.XformPlanarProjection(rs.WorldXYPlane())
        rs.TransformObjects( curves, xform, False )

def checkCurvePosition(objs):

    layers = []
    selection = []

    layers_low = []
    selection_low = []

    for i, obj in enumerate(objs):
        if rs.IsCurve(obj):
            if not isCurveOnCPlane(obj):
                # print "Curve {} not on Cplane".format(obj)
                selection.append(obj)
                appendLayer(layers, obj)
                if isCurveBelowCPlane(obj):
                    selection_low.append(obj)
                    appendLayer(layers_low, obj)

    # if any objects below cplane were found, abort
    if len(layers_low) >0:
        rs.SelectObjects(selection_low)
        redraw()

        msg = "there were curves found below C-plane. Milling the router bed might damage the equipment.\n\nPlease check layers:\n"
        for layer in layers_low:
            msg = msg + "- " + layer + " \n"

        if rs.MessageBox(msg, 18, 'Warning') != 5:
           # not 5, button is not ignore
           # do not proceed with export
           return False


    # when an object is found on > 0 layers, prompt for proceed
    if len(layers) > 0:


        rs.SelectObjects(selection)
        redraw()

        list = []
        for layer in layers:
            list.append((layer, False))

        result = rs.CheckListBox(list, "there were non-planar or elevated curves found on layers below do you want to project them to XYplane", "ProjectToCplane")
        project =[]
        if result:
            for item in result:
                if item[1]:
                    project.append(item[0])
            projectLayersToClpane(project)
        else:
            return False

#        msg = "there were non-planar or elevated curves found on layers:\n"
#        for layer in layers:
#            msg = msg + "- " + layer + " \n"
#
#        msg = msg + '\n Do you want to proceed?'
#
#
#        if rs.MessageBox(msg, 1) != 1:
#            # do not proceed with export
#            return False

    return True

def checkCurveIntegrity(objs):

    layers = []
    selection = []
    delete_objs = []

    for i, obj in enumerate(objs):
        if rs.IsCurve(obj):

            # check for disconnected endpoints
            if not rs.IsCurveClosed(obj):
                end = rs.CurveEndPoint(obj)
                start = rs.CurveStartPoint(obj)
                if rs.Distance(start, end)<0.05:
                    #print "Curve {} not on Cplane".format(obj)
                    selection.append(obj)
                    appendLayer(layers, obj)

    if len(selection) > 0:
        rs.SelectObjects(selection)

    rs.EnableRedraw(True)
    rs.EnableRedraw(False)

    # when an object is found on > 0 layers, prompt for proceed
    if len(layers) > 0:
        msg = "curves seem to be closed but are not:\n"
        for layer in layers:
            msg = msg + "- " + layer + " \n"

        msg = msg + '\n Do you want to proceed?'

        if rs.MessageBox(msg, 1) != 1:
            # do not proceed with export
            return False

    # else
    return True

def moveToOrigin(objs):
    #get left bottom

    rs.EnableRedraw(True)
    selection_base = rs.GetPoint("Pick export base point")
    rs.EnableRedraw(False)

	#box = rs.BoundingBox(objs)
    if selection_base:
        #selection_base = [box[0].X, box[0].Y, box[0].Z]
        vector = rs.VectorSubtract(  selection_base, [0,0,0])

        objs = rs.MoveObjects(objs, rs.VectorReverse(vector))
        return True
    else:
        return False

def convertTextToPolylines(obj):

    # get object properties
    text            = rs.TextObjectText(obj)
    pt              = rs.TextObjectPoint(obj)
    origin          = rs.coerce3dpoint([0,0,0])
    ht              = rs.TextObjectHeight(obj)
    object_layer    = rs.ObjectLayer(obj)
    plane           = rs.TextObjectPlane(obj)

    diff = rs.coerce3dpoint([pt.X, pt.Y, pt.Z])

    p1 = rs.WorldXYPlane()
    #restore view cplane
    rs.ViewCPlane(None, p1)

    matrix = rs.XformRotation4(p1.XAxis, p1.YAxis, p1.ZAxis, plane.XAxis, plane.YAxis, plane.ZAxis)

    rs.DeleteObject(obj)

    # split text at enters
    text = text.split('\r\n')
    opts='GroupOutput=No FontName="' + EXPORT_FONT + '" Italic=No Bold=No Height='+ str(ht)
    opts+=" Output=Curves AllowOpenCurves=Yes LowerCaseAsSmallCaps=No AddSpacing=No "

    origin.Y += ht * len(text) - ht*0.35 - 3

    polylines=[]
    for item in text:
        rs.Command("_-TextObject " + opts + '"'+item+'"' + " " + str(origin) , False)
        polylines += rs.LastCreatedObjects()
        origin.Y -= ht *1.6

    rs.ObjectLayer(polylines, object_layer)

    # transform to old position
    rs.TransformObjects(polylines, matrix, copy=False)
    rs.MoveObjects(polylines, diff)


    return polylines

# explode text objects into curves
def explodeTextObjects(objs):
    new_list = []

    for obj in objs:

        if rs.IsText(obj) and rs.LayerVisible( rs.ObjectLayer(obj) ):
            # only export visible layers:
            polylines = convertTextToPolylines(obj)

            for polyline in polylines:
                new_list.append(polyline)

#            if ("CNC" in rs.ObjectLayer(obj)):
#                # rs.GetBoolean(text, "get", True)
#                # result = rs.TextObjectFont(obj, "Machine Tool Gothic")
#
#                # rs.MessageBox('test' + rs.TextObjectText(obj))
#                # polylines = rs.ExplodeText(obj, True)
#
#                polylines = convertTextToPolylines(obj)
#
#                for polyline in polylines:
#                    new_list.append(polyline)
#            else:
#                # add unexploded text
#                new_list.append(obj)
        else:
            new_list.append(obj)

    return new_list

# recurcive explode of blocks
def explodeBlock(objects):

    def explode(objs, li):
        for obj in objs:
            if rs.IsBlockInstance(obj):

                # DIRTY FIX FOR RHINO 5-SR14 522.8390 (5-22-2017)
                temp_objs = rs.ExplodeBlockInstance(obj)

                # rs.UnselectAllObjects()
                # rs.SelectObject(obj)
                # rs.Command("Explode" , False)
                # temp_objs = rs.LastCreatedObjects()

                explode(temp_objs, li)
            else:
                li.append(obj)

        return li

    #create empty list
    li = []

    #redeclare objects list with content of exploded blocks
    return explode(objects, li)

# recurcive explode of blocks
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

# filters only curves and textobjects, converts points to circles
def filterObjects(objs):
    new_list = []
    for obj in objs:
        if rs.LayerVisible( rs.ObjectLayer(obj) ):
            # only export visible layers
            if rs.IsCurve(obj):
                new_list.append(obj)

            elif rs.IsPoint(obj):
                # convert to circle
                layer = rs.ObjectLayer(obj)
                point=rs.coerce3dpoint(obj)

                circle = rs.AddCircle(rs.WorldXYPlane(),3)

                rs.ObjectLayer(circle, layer)
                rs.MoveObject(circle, [point.X, point.Y, point.Z])
                new_list.append(circle)
                rs.DeleteObject(obj)
                # rs.DeleteObject(point)

            else:
                # remove from obj list
                rs.DeleteObject(obj)
        else:
            # remove from obj list
            rs.DeleteObject(obj)

    return new_list

def simplify(objs):
    for obj in objs:
        if rs.IsCurve(obj):
            rs.SimplifyCurve(obj)

def createPockets(m, obj):

    tool_id     = m.group(1)
    operation   = m.group(2)
    z_pos       = m.group(3)

    if operation == 'Inner contour' or operation == 'Pocket' or operation=='Drill':
        surface_id = rs.ExtrudeCurveStraight( obj, (0,0,0), (0, 0, MAT_THICKNESS+2) )
        rs.CapPlanarHoles(surface_id)
        rs.MoveObject(surface_id, (0,0,z_pos))
        
        return surface_id
        
def makeExtrusions(m, obj, material_thickness):

    tool_id     = m.group(1)
    operation   = m.group(2)
    z_pos       = m.group(3)
    
    if operation == 'Outer contour':
        surface_id = rs.ExtrudeCurveStraight( obj, (0,0,0), (0, 0, material_thickness) )
        rs.CapPlanarHoles(surface_id)
        return surface_id        
        
def sweepVolume(crv, tool_id, z_pos):

    tangent = rs.CurveTangent(crv, rs.CurveParameter(crv, 0))
    origin = rs.CurveStartPoint(crv)
    
    block = rs.InsertBlock( tool_id, (0,0,0), scale=(1,1,1) )
    

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
    
    
    
    rs.MoveObject(surface_id, (0,0,z_pos))
    rs.MoveObject(rev, (0,0,z_pos))
    
    
    
    return [surface_id, rev]        

    
    
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
        
def makeEngraves(m, obj):

    tool_id     = m.group(1)
    operation   = m.group(2)
    z_pos       = m.group(3)

    #restore view cplane
    p1 = rs.WorldXYPlane()
    rs.ViewCPlane(None, p1)
            
    subtracts = []        
    if operation == 'Engrave':
        
        # return sweepVolume(obj, tool_id, z_pos)
        
        subcurves = rs.ExplodeCurves(obj, True)
        
        if subcurves:
            
            for crv in subcurves:
                vol = sweepVolume(crv, tool_id, z_pos)
                if vol:
                    subtracts += vol
        
        result = rs.BooleanUnion(subtracts)
        
        return result
           
         
def convertLayers( objs, material_thickness ):
    invalid_layers =[]
    
    # first find relevant layers
    layers = []
    volumes = []
    subtracts = []
    
    # sort objects
    for obj in objs:
        layer_name = rs.ObjectLayer(obj)
        
        # todo's
        # - add Clamex
        m = re.search(  '(\d.\d.\d)\s'+
                        # '.+(Pocket|Engrave|Inner contour|Outer contour|Drill|Saw-X|Saw-Y|Clamex horizontaal|Clamex verticaal).+'+
                        '.+(Pocket|Engrave|Inner contour|Outer contour|Drill|Saw-X|Saw-Y|Clamex horizontaal).+'+
                        '((?<=\s\+)\d+\.?\d*|(?<=\s)d\d+\.?\d*)'
                    , layer_name)

        if m and len(m.groups()) == 3:
            tool_id     = m.group(1)
            operation   = m.group(2)
            z_pos       = m.group(3)
            
            if operation == 'Outer contour':
                volume = makeExtrusions(m, obj, material_thickness)
                if volume:
                    volumes.append(volume) 
            elif operation == "Pocket" or operation == 'Pocket' or operation=='Drill':
                
                pocket =  createPockets(m, obj)
                if pocket:
                    subtracts.append(pocket  )
                    
            elif operation == 'Engrave':
            
                pocket =  makeEngraves(m, obj)
                if pocket:
                    subtracts.append(pocket ) 
        else:
            invalid_layers.append(layer_name)
        
    
    
    # rs.CopyObjects(subtracts)
    
    myset = set(invalid_layers)
    msg = 'layers could not be processed:\n'
    
    for layer in myset:
        msg += '- ' + layer + "\n"
    
    # rs.MessageBox(msg)
    
    
    part = None
    if len(subtracts)> 0:
        part =  rs.BooleanDifference(volumes, subtracts, False)
        rs.DeleteObjects(volumes)
    else:
        part = volumes
    
    if part:
        return part, subtracts
    else:
        rs.MessageBox('part could not be created')
             
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
    copies = explodeBlock( copies )
    
    # filter objects to only curves and points
    copies = filterObjects(copies) 
    if not checkCurvePosition(copies):
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
            content = explodeBlock( [copy] )
            
            # filter objects to only curves and points
            copies = filterObjects(content) 

            simplify(copies)

            result, subtracts = convertLayers(copies, material_thickness)
            
            set_volumes.append(result)
            set_subtracts.append(subtracts)
             
            rs.DeleteObjects(copies)    
            
            # addResultToBlock(obj, result)
            
        else:
            # add warning message collision check
            print obj
    
    rs.UnselectAllObjects()
    intersect = None
    for i, volume in enumerate(set_volumes):
        for j, subtracts in enumerate(set_subtracts):
            if(i != j):
                print rs.ObjectLayer(volume)
                
                intersect = rs.BooleanIntersection(rs.CopyObject(volume), subtracts, False)
                if intersect:
                    rs.SelectObjects(intersect)
                    
                    
            rs.DeleteObjects(subtracts)

            
       
    
    if intersect:
        rs.MessageBox("ERROR")

        
    redraw()
                
            
if __name__ == "__main__":
    main();
