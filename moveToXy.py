"""
@name:          checkandexport
@description:   exports curves for TheNewMakers milling template
@author:        tim castelijn
@version:       0.6
@link:          https://github.com/timcastelijn/rhinoscript
@notes:         Works with Rhino 5.

"""

# V0.6.1
# - added projectToCplane

# V0.6
# - added text to line convert

# to install as command (alias) or keyboard shortcut, use line below and change to your script file path

# '_-runPythonScript "E:/rhinoscript/moveToXy.py"
# '_-runPythonScript "E:/rhinoscript/checkAndExport.py" _proceed _Enter


import rhinoscriptsyntax as rs
import Rhino
import math
import re
import time
import scriptcontext


def getLowestPoint(obj):
    box = rs.BoundingBox(obj)
    min = 1e20
    lowest = None
    if box:
        for i, point in enumerate(box):
            if point.Z < min:
                min = point.Z
                lowest = point
    
    return lowest
                
# main script
def main():

    # get objects to export
    objs = rs.GetObjects("select objects to move to worldXY", 0, True, True)
    if not objs: print "moveToXY aborted"; return
    
    rs.EnableRedraw(False)

    # reset world xy
    rs.ViewCPlane(None, rs.WorldXYPlane())
        
    for obj in objs:

        
        # get lowest point
        point = getLowestPoint(obj)

        # move object to xy plane
        rs.MoveObject(obj, (0,0, -point.Z))
        
    rs.EnableRedraw(True)

   


if __name__ == "__main__":
    main();
