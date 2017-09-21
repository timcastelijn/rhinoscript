import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import math

# V0.1
# to install as command (alias) or keyboard shortcut, use line below and change to your script file path

# '_-runPythonScript "/Users/timcastelijn/Documents/programming/rhinoscript/checkAndExport.py"
# '_-runPythonScript "E:/checkAndExport.py"

def setCurveDir(objs):
    count = 0
    for obj in objs:

        # if rs.IsCurve(obj) and rs.IsCurvePlanar(obj):
        if rs.IsCurve(obj) and rs.IsCurvePlanar(obj):
            normal = rs.CurveNormal(obj)

            if normal and normal[2] < 0:
                count += 1
                rs.ReverseCurve(obj)
                normal2 = rs.CurveNormal(obj)

                print "Curve {} flipped {}{}".format(obj, normal, normal2)

    print "reversed " + str(count) + " curves"

    # rs.SelectObjects(objs)
    # rs.Command("Dir")

def isCurveOnCPlane(obj):
	data = rs.CurvePoints(obj)
	for pt in data:
		if(math.fabs( pt.Z )> 1e-6 ):
			return False

	return True


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
    for obj in objs:
        if rs.IsCurve(obj):
            if not isCurveOnCPlane(obj):
                # print "Curve {} not on Cplane".format(obj)
                selection.append(obj)
                appendLayer(layers, obj)

        elif rs.IsPoint(obj):
            if not isPointOnCplane(obj):
    			# print "Curve {} not on Cplane".format(obj)
                rs.SelectObject(obj)
                appendLayer(layers, obj)
        else:
            print "object {} is not a curve or point. {}".format(obj, rs.ObjectType(obj) )
	
    if len(selection) > 0:
        rs.SelectObjects(selection)
			
    # when an object is found on > 0 layers, prompt for proceed
    if len(layers) > 0:
        msg = "there were non-planar or elevated curves found on layers:\n"
        for layer in layers:
            msg = msg + "- " + layer + " \n"
			
        msg = msg + '\n Do you want to proceed?'

        if rs.MessageBox(msg, 1) != 1:
            return False

    # else
    return True


def copyToOrigin(objs):

	#get left bottom
	selection_base = rs.GetPoint("Pick export base point")
	#box = rs.BoundingBox(objs)
	if selection_base:
		#selection_base = [box[0].X, box[0].Y, box[0].Z]
		vector = rs.VectorSubtract(  selection_base, [0,0,0])
		
		return rs.CopyObjects(objs, rs.VectorReverse(vector))	

	
def main():
    print("script_start")
    objs = rs.GetObjects("select objects to export", 0, True, True)
	
    if not objs:
        print "abort"
    	return
	
	# check curves for deviation from c-plane
    result = checkCurvePosition(objs);

	# if ok, start export
    if result:		
		#make curve direction all the same
        setCurveDir(objs);

        rs.UnselectAllObjects()

		# move to origin		
        objs = copyToOrigin(objs);
		
		# export
        rs.SelectObjects(objs)		
        rs.Command("Export")
		
        rs.DeleteObjects(objs)
    else:
        print "abort"
    	return
		
if __name__ == "__main__":
    main();
