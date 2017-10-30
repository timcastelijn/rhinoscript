import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import math
import time
import re


def setCurveDir(objs):
    count = 0
    for obj in objs:
        if rs.IsCurve(obj) and rs.IsCurvePlanar(obj):
            if rs.IsCurve(obj):
                normal = rs.CurveNormal(obj)
                
                print normal

                if normal and normal[2] < 0:
                    count += 1
                    # rs.ReverseCurve(obj)

                    # print "Curve {} flipped {}{}".format(obj, normal, normal2)

    print "reversed " + str(count) + " curves"
    
def main():

    objs = rs.GetObjects("select objects to export", 0, True, True)
    if not objs: print "checkAndExport aborted"; return
    
    setCurveDir(objs)

if __name__ == "__main__":
    main();