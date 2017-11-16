import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import math
import time
import re

# '_-runPythonScript "E:/rhinoscript/curvedir_test.py"

def setCurveDir(objs):
    count = 0
    for obj in objs:
        if rs.IsCurve(obj) and rs.IsCurvePlanar(obj):
            
            sp =  rs.AddPoint(rs.CurveEndPoint(obj))

            tangent = rs.CurveTangent(obj, rs.CurveDomain(obj)[0])
            print tangent
            
            p2 = rs.CopyObject(sp, tangent*-10 )
            
            rs.AddPoint(p2)
            
            # rs.Command("Dir")
            # for i in range(0,rs.PolyCurveCount(obj)):
                # l = rs.CurveLength(obj,i)
                # if l < 4:   
                    # print l

            # layer=rs.ObjectLayer(obj)
            # segments = rs.ExplodeCurves(obj, True)
            # obj = rs.JoinCurves(segments, True)
            # rs.ObjectLayer(obj, layer)

            # rs.ObjectLayer(obj, layer)
            
                        
            normal = rs.CurveNormal(obj)           
            result = rs.CurveAreaCentroid(obj)
            
            
            if result:
                print normal
            
                start = result[0]
                end = (result[0].X + 100*normal[0] ,result[0].Y+ 100*normal[1],result[0].Z + 100*normal[2])
                rs.AddLine(result[0], end)
                if normal and normal[2] < 0:
                    count += 1
                    rs.ReverseCurve(obj)

                    # print "Curve {} flipped {}{}".format(obj, normal, normal2)
            
            # try to find discontinuities

    print "reversed " + str(count) + " curves"
    
def main():

    objs = rs.GetObjects("select objects to export", 0, True, True)
    if not objs: print "checkAndExport aborted"; return
    rs.EnableRedraw(False)
    setCurveDir(objs)
    rs.EnableRedraw(True)

if __name__ == "__main__":
    main();