import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import math
import time
import re

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

def createBiesseLayer(m):

    tool_table = importTools("tool_table.txt")
    if not tool_table:
        print 'tool table invalid, abort'
        return False
        
    tool_id     = m.group(1)
    operation   = m.group(2)
    z_pos       = m.group(3)
    
    str = 'TCH'
        
    if operation=="Drill":
        str += '[BG]'
    elif operation=="Saw-X" or operation=="Saw-Y":
        str += '[CUT_G]'
    else:
        str += '[ROUT]'
    
    # workpiece side parameter, 0 by default
    str += '(SIDE)0'
    
    # side of curve parameter CRC
    # 0=center, 1=left, 2 = right, curve direction is always CCW so inside is left
    str += '(CRC)'
    str += {
      'Pocket': "1",
      'Inner contour': "1",
      'Outer contour': "2",
      'Engrave': "0",
      'Drill': "0",
      'Saw-X': "0",
      'Saw-Y': "0",
    }[operation]
        
    # if operation == 'Pocket':
        # parameters['method'] = 'remove_all' 
    
    # depth parameter
    depth = re.search( 'd(\d+\.?\d*)', z_pos)
    if depth:
        # workpiece top -depth, set parameter "TH" to workpiece height and use z_pos as depth
        if not workpiece_thickness:
            workpiece_thickness = rs.GetReal('Please ener the workpiece thickness (TH), to create depth operation')
        
        if workpiece_thickness:
            str += '(DP)' + depth.group(1)
            str += '(TH)' + workpiece_thickness
        else:
            print 'abort'
            return False
    else:
        # workpiece bottom +depth, parameter "TH" is 0 by default and use z_pos as depth from bottom
        str += '(DP)-' + z_pos
    
    # tool name paramter
    if tool_table[tool_id] and tool_table[tool_id]["TNM"]:
        str += '(TNM)$%s$' % tool_table[tool_id]["TNM"]
    else:
        msg += 'tool_id %s not in tool table file or TNM not formatted correctly' % tool_id
    
    # diameter parameter
    # todo: is this required??
    if tool_table[tool_id]["DIA"] and tool_table[tool_id]["DIA"]:
        str += '(DIA)' + tool_table[tool_id]["DIA"]
    else:
        msg += 'tool_id %s not in tool table file or DIA not formatted correctly' % tool_id
    
    return  str            
            
            
            
def convertLayers( objs ):

    # first find relevant layers
    layers = []
    for obj in objs:
        layer_name = rs.ObjectLayer(obj)
        if layer_name not in layers:
            layers.append(layer_name)
    
    # get all layers
    workpiece_thickness = None
    invalid_lines = ''
    for layer in layers:

        # todo's
        # - add drill
        # - add saw blade
        
        m = re.search(  '(\d\d.\d\d)\s'+
                        '.+(Pocket|Engrave|Inner contour|Outer contour|Drill|Saw-X|Saw-Y).+'+
                        # '-\s(.*)\s\S*'+
                        '((?<=\s\+)\d+\.?\d*|(?<=\s)d\d+\.?\d*)'
                    , layer)
        
        if m and len(m.groups()) == 3:
            
            biesselayer = rs.AddLayer( createBiesseLayer(m) )
            for obj in objs:
                if rs.ObjectLayer(obj) == layer:
                    rs.ObjectLayer(obj, biesselayer)
        else:
            invalid_lines += '- ' + layer + '\n'
        
    if len(invalid_lines)>0:
        rs.MessageBox('layers have incorrect format and will not be exported:\n' + invalid_lines + '')
        return False
            

def importTools(filename):
    tool_table={}
    invalid_lines =''
    with open(filename) as fp: 
        # read header
        line = fp.readline()
        # read first line
        line = fp.readline()
        cnt = 1
        while line:
            # print line
            m = re.search(  '(\d\d.\d\d)\t'+
                '(.+)\t'+
                '(.+)'
                , line)
            if m and len(m.groups())>=3:
                tool_table[m.group(1)] = {"TNM":m.group(2), "DIA":m.group(3)}
            else:
                invalid_lines += line +'\n'
                
            line = fp.readline()
            cnt += 1

        if len(invalid_lines)>0:
            rs.MessageBox('lines could not be read, please check the tool table file:\n' + invalid_lines + '')
            return False
                
        return tool_table
    
        
# main script
def main():
    
    # open the file
    # filename = rs.OpenFileName()
    
    # if filename:
        # with open(filename) as f:
            # lines = f.readlines()
            

    # copies = []
    
    

    objs = rs.GetObjects("select objects to export", 0, True, True)
    if not objs: print "checkAndExport aborted"; return



        
    convertLayers( objs)
    
    print 'done'
    print "\n"
        
    

    # copies = explodeBlock(copies)
    
    # copies = explodeTextObjects(copies)
    
    # copies = filterObjects(copies)
     
    # proceed = checkCurvePosition(copies);

    # if proceed:

        # simplify(copies)
            
        # setCurveDir(copies);

        # result = moveToOrigin(copies);

        # if result:
                    
            # rs.SelectObjects(copies)
            # result = rs.Command("Export")
            # if result: print 'exported succesfully'
            
            # return True
    

            
    # rs.DeleteObjects(copies)
    # rs.EnableRedraw(True)

    

if __name__ == "__main__":
    main();
