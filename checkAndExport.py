# V0.5
# to install as command (alias) or keyboard shortcut, use line below and change to your script file path

# '_-runPythonScript "E:/rhinoscript/checkAndExport.py"
# '_-runPythonScript "E:/rhinoscript/checkAndExport.py" _proceed _Enter

import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import math
import re


# function to reverse a curve if the normal points downwards in Z-dir
# assumed is that only closed curves can have inside or outside
def setCurveDir(objs):
    rs.UnselectAllObjects()
    count = 0

    for obj in objs:
        if rs.IsCurve(obj) and rs.IsCurveClosed(obj):

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
        
        if rs.IsPoint(obj):
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
            if ("CNC" in rs.ObjectLayer(obj)):
                # rs.GetBoolean(text, "get", True)
                # result = rs.TextObjectFont(obj, "MecSoft_Font-1")

                polylines = rs.ExplodeText(obj, True)

                for polyline in polylines:
                    new_list.append(polyline)
            else:
                # add unexploded text
                new_list.append(obj)
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
        elif rs.IsText(obj):
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

    action = 'TCH'

    if operation=="Drill":
        action += '[BG]'
    elif operation=="Saw-X" or operation=="Saw-Y":
        action += '[CUT_G]'
    elif operation=="Clamex horizontaal":
        action += '[ROUTG]'
    elif operation=='Pocket':
        action += '[POCK]'
        action += '(DLT)2'
        action += '(TYP)3'
    else:
        action += '[ROUTG]'
        
        # side of curve parameter CRC
        # 0=center, 1=right, 2 = left, curve direction is always CCW so inside is left
        action += '(CRC)'
        action += {
          'Pocket': "1",
          'Inner contour': "1",
          'Outer contour': "2",
          'Engrave': "0",
          'Drill': "0",
          'Saw-X': "0",
          'Saw-Y': "0",
          'Clamex horizontaal': "0",
        }[operation]
        
    action += '(ID)$A%s-%s-%s$' % (m.group(1),m.group(2),m.group(3) )
    action += '(GID)$G%s-%s-%s$' % (m.group(1),m.group(2),m.group(3))
    
    # diameter parameter
    # todo: is this required??
    if tool_id in tool_table and tool_table[tool_id]["DIA"]:
        action += '(DIA)' + tool_table[tool_id]["DIA"]
    else:
        rs.MessageBox( 'tool_id %s not in tool table file or DIA not formatted correctly.' %  (tool_id) )
        return False
        
    # depth parameter
    depth = re.search( 'd(\d+\.?\d*)', z_pos)
    angle = re.search( 'c(\d+\.?\d*)', z_pos)
    if depth:
        action += '(DP)' + depth.group(1)
    elif angle:
        action += '(DP)0'
    else:
        if float(z_pos)<0.0001:
            action += '(DP)0.1'
        else:
            action += '(DP)LPZ-' + z_pos

    # tool name paramter
    if tool_id in tool_table and tool_table[tool_id]["TNM"]:
        action += '(TNM)$%s$' % tool_table[tool_id]["TNM"]
    else:
        rs.MessageBox( 'tool_id %s not in tool table file or TNM not formatted correctly.' % (tool_id) )
        return False

        
    return  action



def convertLayers( objs ):

    # first find relevant layers
    layers = []
    biesse_layers = []
    for obj in objs:
        layer_name = rs.ObjectLayer(obj)
        if layer_name not in layers:
            layers.append(layer_name)

    # get all layers
    invalid_lines = ''
    for layer in layers:
        # todo's
        # - add Clamex
        m = re.search(  '(\d\d.\d\d)\s'+
                        # '.+(Pocket|Engrave|Inner contour|Outer contour|Drill|Saw-X|Saw-Y|Clamex horizontaal|Clamex verticaal).+'+
                        '.+(Pocket|Engrave|Inner contour|Outer contour|Drill|Saw-X|Saw-Y|Clamex horizontaal).+'+
                        '((?<=\s\+)\d+\.?\d*|(?<=\s)d\d+\.?\d*|(?<=\s)c\d+\.?\d*)'
                    , layer)

        if m and len(m.groups()) == 3:
            
            action_layer_name = createBiesseLayer(m)

            # create new layer
            if action_layer_name:
                geo_layer_name = 'TCH[GEO](ID)$G%s-%s-%s$' % (m.group(1),m.group(2),m.group(3))

                rs.AddLayer( action_layer_name )
                rs.AddLayer( geo_layer_name )
                
                rs.LayerColor(geo_layer_name, rs.LayerColor(layer))
                rs.LayerColor(action_layer_name, rs.LayerColor(layer))

                # assign new layer to objects
                for obj in objs:
                    if rs.ObjectLayer(obj) == layer:
                        rs.ObjectLayer(obj, geo_layer_name)
                        
                # add one point to enable exporting
                circle = rs.AddCircle(rs.WorldXYPlane(),3)
                rs.ObjectLayer(circle , action_layer_name)
                objs.append(circle)
                
                # add to table for deleting layers later on
                biesse_layers.append(geo_layer_name)
                biesse_layers.append(action_layer_name)
                       
            else:
                return False
        else:
            invalid_lines += '- ' + layer + '\n'

    if len(invalid_lines)>0:
        msg =   'layers have incorrect format and will not be converted for export:\n' + invalid_lines + '\n'
        msg+=   'correct format is: "<xx.xx> - <operation> - <+|d><x.xx>"\n'
        msg+=   'where operation must be "Pocket|Engrave|Inner contour|Outer contour|Drill|Saw-X|Saw-Y"'

        rs.MessageBox(msg)

    return biesse_layers


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

    # create globally used array of copies
    copies = []
    biesse_layers=[]


    # promt convert for biesse
    convert_for_biesse = rs.GetBoolean("convert layer names for Biesseworks", (['proceed', 'no', 'yes']), (False) )[0]
    
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

            if convert_for_biesse :
                biesse_layers = convertLayers(copies)

            if result:

                # export
                rs.SelectObjects(copies)
                result = rs.Command("Export")
                if result: print 'exported succesfully'

    rs.DeleteObjects(copies)

    if len(biesse_layers)>0:
        for layer in biesse_layers:
            rs.PurgeLayer(layer)

    rs.EnableRedraw(True)


if __name__ == "__main__":
    main();
