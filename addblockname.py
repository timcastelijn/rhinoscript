import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import math

# '_-runPythonScript "/Users/timcastelijn/Documents/programming/rhinoscript/checkAndExport.py"


def setCurveDir(objs):
    count = 0
    for obj in objs:

        # if rs.IsCurve(obj) and rs.IsCurvePlanar(obj):
        if rs.IsCurve(obj) and rs.IsCurvePlanar(obj):
            normal = rs.CurveNormal(obj)

            if normal and normal[2] == -1:
                count += 1
                rs.ReverseCurve(obj)
                normal2 = rs.CurveNormal(obj)

                print "Curve {} flipped {}{}".format(obj, normal, normal2)

    print "reversed " + str(count) + " curves"

    # rs.SelectObjects(objs)
    # rs.Command("Dir")

def isCurveOnCPlane(obj):

    if not rs.IsCurvePlanar(obj):
        return False
    else:
        data = rs.CurvePoints(obj)
        for pt in data:
            if(math.fabs( pt.Z )> 1e-6 ):
                print "Point height: {}".format(pt.Z)
                return False

        return True


def isPointOnCplane(obj):
    return (math.fabs( obj.Z ) > 1e06)

def appendLayer(layers, obj):
    layer = rs.ObjectLayer(obj)
    try:
        layers.index(layer)
        pass
    except Exception as e:
        layers.append( rs.ObjectLayer(obj) )


def checkCurvePosition(objs):
    layers = []
    for obj in objs:
        if rs.IsCurve(obj):
            if not isCurveOnCPlane(obj):
                # print "Curve {} not on Cplane".format(obj)
                rs.SelectObject(obj)
                appendLayer(layers, obj)

        elif rs.IsPoint(obj):
            if not isPointOnCplane(obj):
                # print "Curve {} not on Cplane".format(obj)
                rs.SelectObject(obj)
                appendLayer(layers, obj)
        else:
            print "object {} is not a curve or point".format(obj)

    # when an object is found on > 0 layers, prompt for proceed
    if len(layers) > 0:
        msg = "there were curves found on layers:\n"
        for layer in layers:
            msg = msg + "- " + layer + " \n"

        if rs.MessageBox(msg, 1) != 1:
            return False

    # else
    return True


def exportToDxf(objs):

    rs.SelectObjects(objs)

    # rs.SaveFileName(extension".dxf")

    # rs.Command("-_export /documents/acdf.dxf")
    rs.Command("'_export")

    # Rhino.DocumentSaveEventArgs.ExportSelected(__new__)
    # Rhino.DocumentSaveEventArgs.ExportSelected()


def main():
    objs = rs.GetObjects("select block", 0, True, True)
    print len(objs)

    for obj in objs:
        if rs.ObjectType(obj) == 4096:
            name =  rs.BlockInstanceName(obj)
            print rs.BlockDescription(name)
            children = rs.ExplodeBlockInstance(obj)
            text = rs.AddText(name, [0,0,0], height=1.0, font="Arial", font_style=0, justification=None)

            print type(children)

            children.Append( text)
            print children[0]

            # point = rs.GetPoint("Block base point")
            # block = rs.AddBlock(children, point, name, True)
            # rs.InsertBlock(name,point)

if __name__ == "__main__":
    main();
