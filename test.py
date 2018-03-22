import rhinoscriptsyntax as rs


obj = rs.GetObject('select')

def checkSelfIntersection(obj):
    segments = rs.ExplodeCurves(obj, False)

    list = segments
    for seg in segments:
        segA = seg
        segments.remove(segA)
        
        for segB in segments:
            intersection_list = rs.CurveCurveIntersection(segA, segB, tolerance=-1)
            if intersection_list:
                for intersection in intersection_list:
                    if (intersection[0] == 2):
                        rs.AddPoint(intersection[1])
                        rs.AddPoint(intersection[2])

    rs.DeleteObjects(list)


checkSelfIntersection(obj)