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

    # get script location
    
    
    rs.AddAlias("MoveToWorldXY",  "E:/rhinoscript/moveToXy.py")


   


if __name__ == "__main__":
    main();
