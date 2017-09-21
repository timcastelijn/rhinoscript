import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import math


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

def checkCurvePosition(objs):
    layers = []
    for obj in objs:
        if rs.IsCurve(obj):
            if not isCurveOnCPlane(obj):
                # print "Curve {} not on Cplane".format(obj)
                rs.SelectObject(obj)
                layers.append( rs.ObjectLayer(obj) )
        elif rs.IsPoint(obj):
            if not isPointOnCplane(obj):
                # print "Curve {} not on Cplane".format(obj)
                rs.SelectObject(obj)
                layers.append( rs.ObjectLayer(obj) )
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
    objs = rs.GetObjects("select objects", 0, True, True)

    print("script_start")

    setCurveDir(objs);

    result = checkCurvePosition(objs);

    if result:
        rs.SelectObjects(objs)

        # rs.SaveFileName(extension".dxf")

        # rs.Command("-_export /documents/acdf.dxf")
        rs.Command("'_export")

if __name__ == "__main__":
    main();
