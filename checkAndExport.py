import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import math
import time

# V0.3
# to install as command (alias) or keyboard shortcut, use line below and change to your script file path

# '_-runPythonScript "/Users/timcastelijn/Documents/programming/rhinoscript/checkAndExport.py"
# '_-runPythonScript "E:/checkAndExport.py"
# '_-runPythonScript "C:/checkAndExport.py"


# function to reverse a curve if the normal points downwards in Z-dir
# assumed is that only closed curves can have inside or outside 
def setCurveDir(objs):
    rs.UnselectAllObjects()
    count = 0
    for obj in objs:
        if rs.IsCurve(obj):
            if rs.IsCurveClosed(obj):
                normal = rs.CurveNormal(obj)
                if normal and normal[2] < 0:
                    count += 1
                    rs.ReverseCurve(obj)
                    rs.SelectObject(obj)

    rs.EnableRedraw(True)
    rs.EnableRedraw(False)
    
    rs.MessageBox( "resvered curves  " + str(count) + " curves")

    # rs.SelectObjects(objs)
    # rs.Command("Dir")


def isCurveOnCPlane(obj):
    if rs.IsCurvePlanar(obj):
        data = rs.CurvePoints(obj)
        for pt in data:
            if(math.fabs( pt.Z )< 1e-8 ):
                return True
    
	return False


def isPointOnCplane(obj):
    return (math.fabs( rs.PointCoordinates(obj)[2] ) < 1e-8)

def appendLayer(layers, obj):
    layer = rs.ObjectLayer(obj)
    try:
        layers.index(layer)
        pass
    except Exception as e:
        layers.append( rs.ObjectLayer(obj) )


def checkCurvePosition(objs):

    layers = []
    selection = []
    delete_objs = []
    
    for i, obj in enumerate(objs):
        if rs.IsCurve(obj):
            if not isCurveOnCPlane(obj):
                # print "Curve {} not on Cplane".format(obj)
                selection.append(obj)
                appendLayer(layers, obj)
        else:
            # must be point rs.IsPoint(obj):
            if not isPointOnCplane(obj):
    			# print "Curve {} not on Cplane".format(obj)
                # rs.SelectObject(obj)
                selection.append(obj)
                appendLayer(layers, obj)
             
    if len(selection) > 0:
        rs.SelectObjects(selection)
        
    rs.EnableRedraw(True)
    rs.EnableRedraw(False)
    
    # when an object is found on > 0 layers, prompt for proceed
    if len(layers) > 0:
        msg = "there were non-planar or elevated curves found on layers:\n"
        for layer in layers:
            msg = msg + "- " + layer + " \n"

        msg = msg + '\n Do you want to proceed?'

        if rs.MessageBox(msg, 1) != 1:
            # do not proceed with export
            return False

    # else
    return True

def diff(first, second):
        second = set(second)
        return [item for item in first if item not in second]
    
def checkCurveIntegrity(objs):

    layers = []
    selection = []
    delete_objs = []
    
    for i, obj in enumerate(objs):
        if rs.IsCurve(obj):
        
            # points = rs.CurveDiscontinuity(obj, 5)
            # if points: 
                # rs.AddPoints(points)
                
                # points2 = rs.CullDuplicatePoints(points)
                # points3 = diff(points, points2)
                # if points3: 
                    # rs.AddPoints(points3)
                    # return False
            
            
            # check for disconnected endpoints
            if not rs.IsCurveClosed(obj):
                end = rs.CurveEndPoint(obj)
                start = rs.CurveStartPoint(obj)
                if rs.Distance(start, end)<0.1:
                    #print "Curve {} not on Cplane".format(obj)
                    selection.append(obj)
                    appendLayer(layers, obj)
            # check for too small curvelengths
            # i=0
            # while True:
                # try:
                    # leng = rs.CurveLength(obj,i)
                    # if len < 0.02:
                        # print len
                        # selection.append(obj)
                        # appendLayer(layers, obj)
                        # break
                # except:
                    # break
                # i+=1
             
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

# explode text objects into curves
def explodeTextObjects(objs):
    
    new_list = []
    
    for obj in objs:
        if rs.IsText(obj):
            # if ("CNC" in rs.ObjectLayer(obj)):
            # rs.GetBoolean(text, "get", True)
            # result = rs.TextObjectFont(obj, "MecSoft_Font-1")
            
            polylines = rs.ExplodeText(obj, True)
            
            for polyline in polylines:
                new_list.append(polyline)
        else:
            new_list.append(obj)
            
    return new_list
                
                
# recurcive explode of blocks
def explodeBlock(objects):
	
    def explode(objs, li):
        for obj in objs:
            if rs.IsBlockInstance(obj):
                temp_objs = rs.ExplodeBlockInstance(obj)
                explode(temp_objs, li)
            else:
                li.append(obj)
        return li
        
    #create empty list                
    li = []

    #redeclare objects list with content of exploded blocks
    return explode(objects, li) 
    
def filterObjects(objs):
    new_list = []
    for obj in objs:
        if rs.IsCurve(obj):
            new_list.append(obj)

        elif rs.IsPoint(obj):
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
         
    return new_list
 
def simplify(objs): 
    for obj in objs:
        if rs.IsCurve(obj):
            rs.SimplifyCurve(obj)
    
# main script
def main():
    
    # create globally used array of copies
    copies = []

    # get objects to export
    objs = rs.GetObjects("select objects to export", 0, True, True)
    if not objs: print "checkAndExport aborted"; return

    rs.EnableRedraw(False)

    # create copies of all block contents
    copies = rs.CopyObjects(objs)

    
    # explodeblock
    copies = explodeBlock(copies)
    
    copies = explodeTextObjects(copies)
    
    copies = filterObjects(copies)
     
    if checkCurveIntegrity(copies):
    
        # check curves for deviation from c-plane
        proceed = checkCurvePosition(copies);

        # if ok, start export
        if proceed:
            # rs.UnselectAllObjects()

            simplify(copies)
                
            setCurveDir(copies);

            # move to origin
            result = moveToOrigin(copies);

            if result:
                        
                # export
                rs.SelectObjects(copies)
                result = rs.Command("Export")
                if result: print 'exported succesfully'
            
    rs.DeleteObjects(copies)
    rs.EnableRedraw(True)


if __name__ == "__main__":
    main();
