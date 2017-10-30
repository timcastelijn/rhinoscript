import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import math
import time

# V0.1
# to install as command (alias) or keyboard shortcut, use line below and change to your script file path

# '_-runPythonScript "/Users/timcastelijn/Documents/programming/rhinoscript/checkAndExport.py"
# '_-runPythonScript "E:/checkAndExport.py"


# function to reverse a curve if the normal points downwards in Z-dir
# assumed is that only closed curves can have inside or outside 
def setCurveDir(objs):
    count = 0
    for obj in objs:
        # if rs.IsCurve(obj) and rs.IsCurvePlanar(obj):
        if rs.IsCurve(obj):
            normal = rs.CurveNormal(obj)

            if normal and normal[2] < 0:
                count += 1
                rs.ReverseCurve(obj)

                # print "Curve {} flipped {}{}".format(obj, normal, normal2)

    print "reversed " + str(count) + " curves"

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
    return (math.fabs( rs.PointCoordinates(obj)[2] ) < 1e-6)

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
        if rs.IsCurve(obj) or rs.IsPoint(obj):
            new_list.append(obj)
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
            
            return True
    

            
    rs.DeleteObjects(copies)
    rs.EnableRedraw(True)


if __name__ == "__main__":
    main();
