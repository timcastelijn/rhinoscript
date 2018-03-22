import rhinoscriptsyntax as rs
import re

def convertToPolylines(obj):

    # get object properties
    text            = rs.TextObjectText(obj)
    pt              = rs.TextObjectPoint(obj)
    origin          = rs.coerce3dpoint([0,0,0])
    ht              = rs.TextObjectHeight(obj)
    object_layer    = rs.ObjectLayer(obj)
    plane           = rs.TextObjectPlane(obj)
        
    diff = rs.coerce3dpoint([pt.X, pt.Y, pt.Z])

    p1 = rs.WorldXYPlane()
        
    matrix = rs.XformRotation4(p1.XAxis, p1.YAxis, p1.ZAxis, plane.XAxis, plane.YAxis, plane.ZAxis)


    rs.DeleteObject(obj)
        


    # set current layer to put strings in
    prevlayer = rs.CurrentLayer()
    layer = rs.AddLayer('temptextlayer')
    rs.CurrentLayer('temptextlayer')

    # split text at enters
    text = text.split('\r\n')
    opts='GroupOutput=No FontName="timfont" Italic=No Bold=No Height='+ str(ht)
    opts+=" Output=Curves AllowOpenCurves=Yes LowerCaseAsSmallCaps=No AddSpacing=No "
    
    origin.Y += ht * len(text) *1.2
    for item in text:
        rs.Command("_-TextObject " + opts + '"'+item+'"' + " " + str(origin) , False)
        origin.Y -= ht *1.5
        
    #restore current layer
    rs.CurrentLayer(prevlayer)

    
    #select newly created texts
    polylines = rs.ObjectsByLayer('temptextlayer')
    
    # transform to old position
    rs.TransformObjects(polylines, matrix, copy=False)
    rs.MoveObjects(polylines, diff)
    
    rs.ObjectLayer(polylines, object_layer)
    
    return polylines
    
# '_-runPythonScript "E:/rhinoscript/textobject.py"

    
obj = rs.GetObject('select textobject')

convertToPolylines(obj)