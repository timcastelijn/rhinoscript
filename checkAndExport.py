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

# '_-runPythonScript "E:/rhinoscript/checkAndExport.py"
# '_-runPythonScript "E:/rhinoscript/checkAndExport.py" _proceed _Enter


import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import math
import re
import time
import os

# SCRIPT GLOBALS
EXPORT_FONT = 'timfont'
DEBUG_CLAMEX        = False
DEBUG_FLIPCUVRVE    = False

def redraw():
    rs.EnableRedraw(True)
    rs.EnableRedraw(False)

# function to reverse a curve if the normal points downwards in Z-dir
# assumed is that only closed curves can have inside or outside
def setCurveDir(objs):
    rs.UnselectAllObjects()
    count = 0
    count2 = 0

    for obj in objs:
        if rs.IsCurve(obj) and rs.IsCurveClosed(obj):
        
            # 1 = CW, -1 = CCW, 0 = N/A
            # -1 if the curve's orientation is counter-clockwise
            # 0 if unable to compute the curve's orientation
            if rs.ClosedCurveOrientation(obj) == 0:
                
                if DEBUG_FLIPCUVRVE:
                    rs.SelectObject(obj)
                    return False
                    
                count2 += 1
            if rs.ClosedCurveOrientation(obj) == 1:
                rs.ReverseCurve(obj)
                count += 1
                
                if DEBUG_FLIPCUVRVE:
                    rs.SelectObject(obj)                    

                # normal = rs.CurveNormal(obj)
                # if normal and normal[2] < 0:
                    # count += 1
                    # rs.ReverseCurve(obj)
                    # rs.SelectObject(obj)

    rs.EnableRedraw(True)
    rs.EnableRedraw(False)
    
    print "reversed curves  " + str(count) + " curves"
    
    if DEBUG_FLIPCUVRVE:
        rs.MessageBox( "reversed curves  " + str(count) + " curves")

    if count2 >0 :   
        rs.MessageBox( "Curve direction of " + str(count) + " curves could not be determined")
        
    return True

def isCurveOnCPlane(obj):
    if rs.IsCurvePlanar(obj):
        data = rs.CurvePoints(obj)
        for pt in data:
            if(math.fabs( pt.Z )< 1e-8 ):
                return True

	return False

def isCurveBelowCPlane(obj):
    data = rs.CurvePoints(obj)
    for pt in data:
        if (pt.Z < -1e-8 ):
            return True

	return False

# append objectlayer to list
def appendLayer(layers, obj):
    layer = rs.ObjectLayer(obj)
    try:
        layers.index(layer)
        pass
    except Exception as e:
        layers.append( rs.ObjectLayer(obj) )

def projectLayersToClpane(layers):
    for layer in layers:
        curves = rs.ObjectsByLayer(layer)

        xform = rs.XformPlanarProjection(rs.WorldXYPlane())
        rs.TransformObjects( curves, xform, False )

def checkCurvePosition(objs):

    layers = []
    selection = []

    layers_low = []
    selection_low = []

    for i, obj in enumerate(objs):
        if rs.IsCurve(obj):
            if not isCurveOnCPlane(obj):
                # print "Curve {} not on Cplane".format(obj)
                selection.append(obj)
                appendLayer(layers, obj)
                if isCurveBelowCPlane(obj):
                    selection_low.append(obj)
                    appendLayer(layers_low, obj)

    # if any objects below cplane were found, abort
    if len(layers_low) >0:
        rs.SelectObjects(selection_low)
        rs.ZoomSelected()
        redraw()
        
        rs.UnselectAllObjects()

        msg = "there were curves found below C-plane. Milling the router bed might damage the equipment.\n\nPlease check layers:\n"
        for layer in layers_low:
            msg = msg + "- " + layer + " \n"

        if rs.MessageBox(msg, 18, 'Warning') != 5:
           # not 5, button is not ignore
           # do not proceed with export
           return False


    # when an object is found on > 0 layers, prompt for proceed
    if len(layers) > 0:


        rs.SelectObjects(selection)
        rs.ZoomSelected()
        redraw()
        
        rs.UnselectAllObjects()

        list = []
        for layer in layers:
            list.append((layer, False))

        result = rs.CheckListBox(list, "there were non-planar or elevated curves found on layers below do you want to project them to XYplane", "ProjectToCplane")
        project =[]
        if result:
            for item in result:
                if item[1]:
                    project.append(item[0])
            projectLayersToClpane(project)
        else:
            return False

#        msg = "there were non-planar or elevated curves found on layers:\n"
#        for layer in layers:
#            msg = msg + "- " + layer + " \n"
#
#        msg = msg + '\n Do you want to proceed?'
#
#
#        if rs.MessageBox(msg, 1) != 1:
#            # do not proceed with export
#            return False

    return True


def checkCurveIntegrity(objs):

    layers = []
    selection = []
    delete_objs = []

    for i, obj in enumerate(objs):
        if rs.IsCurve(obj):
            layer_name = rs.ObjectLayer(obj)
            # check for disconnected endpoints
            if(re.search('contour', layer_name , re.IGNORECASE) or re.search('Pocket', layer_name , re.IGNORECASE)) and not rs.IsCurveClosed(obj):
                selection.append(obj)
                appendLayer(layers, obj)
                
                delete_objs.append( rs.AddPoint( rs.CurveStartPoint(obj)) )
                delete_objs.append( rs.AddPoint( rs.CurveEndPoint(obj)) )

    if len(selection) > 0:
        rs.SelectObjects(selection)
        rs.ZoomSelected()
        redraw()

    # when an object is found on > 0 layers, prompt for proceed
    if len(layers) > 0:

        msg = "See selection: curves and contours should always be closed:\n"
        for layer in layers:
            msg = msg + "- " + layer + " \n"

        msg = msg + '\n Do you want to proceed?'
        
        rs.DeleteObjects( delete_objs )

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


def convertTextToPolylines(obj):

    layer = rs.ObjectLayer(obj)
    polylines = rs.ExplodeText(obj, True)
    
    rs.ObjectLayer(polylines, layer)

    return polylines


# DEPRICATED    
def convertTextToPolylines2(obj):

    # get object properties
    text            = rs.TextObjectText(obj)
    pt              = rs.TextObjectPoint(obj)
    origin          = rs.coerce3dpoint([0,0,0])
    ht              = rs.TextObjectHeight(obj)
    object_layer    = rs.ObjectLayer(obj)
    plane           = rs.TextObjectPlane(obj)

    diff = rs.coerce3dpoint([pt.X, pt.Y, pt.Z])

    p1 = rs.WorldXYPlane()
    #restore view cplane
    rs.ViewCPlane(None, p1)

    matrix = rs.XformRotation4(p1.XAxis, p1.YAxis, p1.ZAxis, plane.XAxis, plane.YAxis, plane.ZAxis)

    rs.DeleteObject(obj)

    # split text at enters
    text = text.split('\r\n')
    opts='GroupOutput=No FontName="' + EXPORT_FONT + '" Italic=No Bold=No Height='+ str(ht)
    opts+=" Output=Curves AllowOpenCurves=Yes LowerCaseAsSmallCaps=No AddSpacing=No "

    origin.Y += ht * len(text) - ht*0.35 - 3

    polylines=[]
    for item in text:
        rs.Command("_-TextObject " + opts + '"'+item+'"' + " " + str(origin) , False)
        polylines += rs.LastCreatedObjects()
        origin.Y -= ht *1.6

    rs.ObjectLayer(polylines, object_layer)

    # transform to old position
    rs.TransformObjects(polylines, matrix, copy=False)
    rs.MoveObjects(polylines, diff)


    return polylines

# explode text objects into curves
def explodeTextObjects(objs):
    new_list = []

    for obj in objs:

        if rs.IsText(obj) and rs.LayerVisible( rs.ObjectLayer(obj) ):
            # only export visible layers:
            polylines = convertTextToPolylines(obj)
            # polylines = convertTextToPolylines2(obj)

            for polyline in polylines:
                new_list.append(polyline)

#            if ("CNC" in rs.ObjectLayer(obj)):
#                # rs.GetBoolean(text, "get", True)
#                # result = rs.TextObjectFont(obj, "Machine Tool Gothic")
#
#                # rs.MessageBox('test' + rs.TextObjectText(obj))
#                # polylines = rs.ExplodeText(obj, True)
#
#                polylines = convertTextToPolylines(obj)
#
#                for polyline in polylines:
#                    new_list.append(polyline)
#            else:
#                # add unexploded text
#                new_list.append(obj)
        else:
            new_list.append(obj)

    return new_list

# recurcive explode of blocks
def explodeBlock(objects):

    def explode(objs, li):
        for obj in objs:
            if rs.IsBlockInstance(obj):

            
                # DIRTY FIX FOR RHINO 5-SR14 522.8390 (5-22-2017)
                # temp_objs = rs.ExplodeBlockInstance(obj)

                rs.UnselectAllObjects()
                rs.SelectObject(obj)
                rs.Command("Explode" , False)
                temp_objs = rs.LastCreatedObjects()
                
                explode(temp_objs, li)
            else:
                li.append(obj)

        return li

    #create empty list
    li = []

    #redeclare objects list with content of exploded blocks
    return explode(objects, li)

# filters only curves and textobjects, converts points to circles
def filterObjects(objs):
    new_list = []
    for obj in objs:
        layername = rs.ObjectLayer(obj)
        if rs.LayerVisible( layername ) and not ( re.search('hulp', layername , re.IGNORECASE) )  :
        # if rs.LayerVisible( layername ):
            # only export visible layers
            if rs.IsCurve(obj):
                new_list.append(obj)

            elif rs.IsPoint(obj):
                # convert to circle
                layer = rs.ObjectLayer(obj)
                point=rs.coerce3dpoint(obj)

                circle = rs.AddCircle(rs.WorldXYPlane(),3)

                rs.ObjectLayer(circle, layer)
                rs.MoveObject(circle, [point.X, point.Y, point.Z])
                new_list.append(circle)
                rs.DeleteObject(obj)
                # rs.DeleteObject(point)
            elif rs.IsText(obj) and ( re.search('CNC::', layername , re.IGNORECASE)):
                # only export text if it is in CNC layer
                new_list.append(obj)
            else:
                # remove from obj list
                rs.DeleteObject(obj)
        else:
            # remove from obj list
            rs.DeleteObject(obj)
    
    # for i, obja in enumerate(new_list):
        # for j, objb in enumerate(new_list):
            # if(i != j):
                # if rs.IsCurve(obja) and rs.IsCurve(objb):
                    
                # compare objects:
                
    
    return new_list

def simplify(objs):
    for obj in objs:
        if rs.IsCurve(obj):
            rs.SimplifyCurve(obj)

def getClamexVerAngle(obj):       
    vec_y = (0,-10,0)
    pts = rs.CurveEditPoints(obj)
    
    leng = len(pts)
    
    a=  pts[leng-1]
    b = pts[leng-2]
    
    vec1 = b - a
                
    angle = math.degrees(calcAngle(vec1, vec_y))
    
    # round to 0 digits
    angle = int(round(angle))
    
    return angle
    
def createBiesseLayer(layer_name, tool_id, operation, z_pos, c_angle):

    tool_table = importTools("tool_table.txt")
    if not tool_table:
        print 'tool table invalid, abort'
        return False

    action = 'TCH'

    if operation=="Drill":
        action += '[BG]'
    elif operation=="Saw-X" or operation=="Saw-Y":
        action += '[CUT_G]'
    elif operation=="Clamex verticaal":
        action += '[ROUTG]'
        
        # print c_angle
        action += '(AZ)90'
        action += '(AR)%s' % c_angle
        action += '(CKA)1'      # 1=azrABS, 2=azrINC 
        action += '(THR)0'  
        action += '(AZS)10'  
        action += '(TTP)102'    # 102=ROUT0  DD
        action += '(TIN)0'    # 102=ROUT0  DD
        action += '(TOU)0'    # 102=ROUT0  DD
        
    elif operation=='Pocket':
        action += '[POCK]'
        action += '(DLT)2'                                  # overlap (in mm?)
        action += '(TYP)3'                                  # 0 =ptZIG(arceren), 1=ptZZ(arceren continu), 2=ptIN(concentrisch naar binnen), 3=ptOUT(concentrisch naar buiten), 4=ptFSH(finish)
        # action += '(ZST)%s' % (tool_table[tool_id]["DIA"] - 1)     # overlap 0 =ptZIG(arceren), 1=ptZZ(arceren continu), 2=ptIN(concentrisch naar binnen), 3=ptOUT(concentrisch naar buiten), 4=ptFSH(finish)
        # action += '(VTR)%s' % (tool_table[tool_id]["DIA"])     # travel distance 0 =ptZIG(arceren), 1=ptZZ(arceren continu), 2=ptIN(concentrisch naar binnen), 3=ptOUT(concentrisch naar buiten), 4=ptFSH(finish)

    else:
        action += '[ROUTG]'
        action += '(TIN)7'    # 102=ROUT0  DD
        action += '(TOU)7'    # 102=ROUT0  DD
        # side of curve parameter CRC
        # 0=center, 1=right, 2 = left, curve direction is always CCW so inside is left
        action += '(CRC)'
        # action += '(ZST)%s' % (tool_table[tool_id]["DIA"])     # Overlap
        action += {
          'Pocket': "1",
          'Inner contour': "1",
          'Outer contour': "2",
          'Engrave': "0",
          'Clamex horizontaal': "0",
          'Clamex verticaal': "0",
          'Drill': "0",
          'Saw-X': "0",
          'Saw-Y': "0",
        }[operation]

    # assign action ID and geometry ID
    action += '(ID)$A%s$' % (layer_name )
    action += '(GID)$G%s$' % (layer_name)

    # diameter parameter
    # todo: is this required??
    if tool_id in tool_table and tool_table[tool_id]["DIA"]:
        action += '(DIA)' + tool_table[tool_id]["DIA"]
    else:
        rs.MessageBox( 'tool_id %s not in tool table file or DIA not formatted correctly.' %  (tool_id) )
        return False

    
        
    # depth parameter
    depth = re.search( 'd(\d+\.?\d*)', z_pos)
    if depth:
        # depth from top of workpiece
        action += '(DP)' + depth.group(1)
    else:
        if operation ==  'Clamex horizontaal' or operation ==  'Clamex verticaal':
            action += '(DP)LPZ'
        elif abs(float(z_pos))<0.0001:
            # set any 0 depth to 0.1
            action += '(DP)LPZ+0.1'
        else:
            action += '(DP)LPZ-' + z_pos
            
            
    # tool name paramter
    if tool_id in tool_table and tool_table[tool_id]["TNM"]:
        action += '(TNM)$%s$' % tool_table[tool_id]["TNM"]
    else:
        rs.MessageBox( 'tool_id %s not in tool table file or TNM not formatted correctly.' % (tool_id) )
        return False


    return  action
    
def getDefault16():
    tools = [
        "0.0.1 - 16DIAMANT", 
        "0.0.2 - 16LANG",
        "0.0.3 - DIA16SPIRA",
        "0.0.4 - 16DIAM2",
        "0.0.5 - 16Z2",
    ]
    
    tool16 = rs.ComboListBox(tools, "generic 16mm is detected. Specify a 16mm tool")
    if tool16: 
        return tool16[:5]    
    
def convertLayers( objs ):
    
    # get specific tool if none specified
    tool16 = getDefault16()
    if not tool16: return False
    
    
    # first find relevant layers
    layers = []
    biesse_layers = []
    for obj in objs:
        layer_name = rs.ObjectLayer(obj)
        if 'Clamex verticaal' in layer_name: 
            # create a layer with clamex c-angle
            layer_name = layer_name + ' c%s' % getClamexVerAngle(obj)
            
            # create a new layer with this name
            if not rs.IsLayer(layer_name):
                rs.AddLayer(layer_name)
                biesse_layers.append(layer_name)
                print layer_name
            
            #add the object to this layer
            rs.ObjectLayer(obj, layer_name)
        
        
        if '0.0.0' in layer_name:
            layer_name = layer_name.replace("0.0.0", tool16)
            
            # create a new layer with this name
            if not rs.IsLayer(layer_name):
                rs.AddLayer(layer_name)
                biesse_layers.append(layer_name)
            
            print layer_name
            #add the object to this layer
            rs.ObjectLayer(obj, layer_name)
            
        if layer_name not in layers:
            layers.append(layer_name)
            
            
    # get all layers
    invalid_lines = ''
    for layer_name in layers:
        # todo's
        # - add Clamex
        m = re.search(  '(\d.\d.\d)\s'+
                        '.+(Pocket|Engrave|Inner contour|Outer contour|Drill|Saw-X|Saw-Y|Clamex horizontaal|Clamex verticaal).+'+
                        '.+((?<=\s\+)\d+\.?\d*|(?<=\s)d\d+\.?\d*)'+
                        '\s*c?(-?\d+)*'
                    , layer_name)

        if m and len(m.groups()) >= 3:
        
            tool_id     = m.group(1)
            operation   = m.group(2)
            depth       = m.group(3)
            c_angle     = m.group(4) or None

            action_layer_name = createBiesseLayer(layer_name, tool_id, operation, depth, c_angle)

            if action_layer_name:
                # create new geo layer
                geo_layer_name = 'TCH[GEO](ID)$G%s$' % (layer_name)

                rs.AddLayer( action_layer_name )
                rs.AddLayer( geo_layer_name )

                # add layers to list for deleting layers later on
                biesse_layers.append(geo_layer_name)
                biesse_layers.append(action_layer_name)

                rs.LayerColor(geo_layer_name, rs.LayerColor(layer_name))
                rs.LayerColor(action_layer_name, rs.LayerColor(layer_name))

                # move objects to new geo layer
                for obj in objs:
                    if rs.ObjectLayer(obj) == layer_name:
                        rs.ObjectLayer(obj, geo_layer_name)

                # add one point to enable exporting of the action layer
                circle = rs.AddCircle(rs.WorldXYPlane(),3)
                rs.ObjectLayer(circle , action_layer_name)
                objs.append(circle)


            else:
                return False
        else:
            invalid_lines += '- ' + layer_name + '\n'

    if len(invalid_lines)>0:
        msg =   'layers have incorrect format and will not be converted for export:\n' + invalid_lines + '\n'
        msg+=   'correct format is: "<x.x.x> - <operation> - <+|d><x.xx>"\n'
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
            m = re.search(  '(\d.\d.\d)\t'+
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

def vecLen(a):
    return math.sqrt(sum( [ math.pow(a[i],2) for i in range(len(a))] ))    

# function to calculate an angle between two vectors
    
def calcAngle(vec1, vec2):
    
    dotpr = sum( [vec1[i]*vec2[i] for i in range(len(vec2))] )
    theta = math.acos( dotpr / (vecLen(vec1) * vecLen(vec2) ) )
    
    
    # for y component of vec1
    if vec1[0]>0:
        theta = -theta
    
    
    return theta           
        
def extractClamexOrientation(objs):
    vec_x = [-10,0,0]
    data = []    
    result = False
        
    for obj in objs:
        if 'Clamex verticaal' in rs.ObjectLayer(obj):
            result = True
            pts = rs.CurveEditPoints(obj)
            
            leng = len(pts)
            
            a=  pts[leng-1]
            b = pts[leng-2]
            
            vec1 = b - a
                        
            angle = math.degrees(calcAngle(vec1, vec_x)) 
            
            richting = 'N/A'
            if angle == 0:
                richting = 'X'
            elif angle == 90:
                richting = 'Y'
            
            print b, angle
            
            data.append('CLAMEX POSX=%.2f POSY=%.2f RICHTING="%s"\n'%( b.X, b.Y, richting))
            
            if DEBUG_CLAMEX:
                rs.AddPoint( b )
    if result:         
        return data

def storeDefaultValues(convert_for_biesse, export_clamex_txt):
    convert_for_biesse  = rs.SetDocumentData("CheckAndExport", "convert_for_biesse", str(convert_for_biesse))
    export_clamex_txt   = rs.SetDocumentData("CheckAndExport", "export_clamex_txt", str(export_clamex_txt))
    
        
def getDefaultValues():
    str_convert_for_biesse  = rs.GetDocumentData("CheckAndExport", "convert_for_biesse")
    str_export_clamex_txt   = rs.GetDocumentData("CheckAndExport", "export_clamex_txt")
    
    convert_for_biesse  = str_convert_for_biesse == 'True'
    export_clamex_txt   = str_export_clamex_txt == 'True'
    
    return (convert_for_biesse, export_clamex_txt)

# joins all curves in the same layer    
def joinCurves(copies):

    # sortobjects per layer
    sorted_objects ={}
    for obj in copies:
        layer_name = rs.ObjectLayer(obj)
        
        if not (layer_name in sorted_objects):
            # add new list
            sorted_objects[layer_name] = []
 
        sorted_objects[layer_name].append(obj)
    
    # join curves per layer
    new_list =[]        
    for layer_name in sorted_objects:
        if len(sorted_objects[layer_name])>1:
            # list is at least 2 items
            list_result = rs.JoinCurves(sorted_objects[layer_name], True)
        else:
            list_result = sorted_objects[layer_name]
        
        for obj in list_result:
            rs.ObjectLayer(obj, layer_name)
            new_list.append(obj)
        
    return new_list    
    
# main script
def main():

    # create globally used array of copies
    copies = []
    biesse_layers=[]


    # promt convert for biesse

    items = (
        ['convert_to_biesse_layers', 'no', 'yes'],
        ['export_clamex_txt', 'no', 'yes'],
    )
    
    
    default_values = getDefaultValues()
    
    
    options = rs.GetBoolean("conversion options", items, default_values )

    if not options or len(options) <2: print "checkAndExport aborted"; return
    
 
    convert_for_biesse  = options[0]
    export_clamex_txt   = options[1]

    storeDefaultValues(convert_for_biesse, export_clamex_txt )

    
    # get objects to export
    objs = rs.GetObjects("select objects to export", 0, True, True)
    if not objs: print "checkAndExport aborted"; return

    rs.EnableRedraw(False)

    # create copies of all block contents
    copies = rs.CopyObjects(objs)

    # explodeblock
    copies = explodeBlock(copies)

    copies = explodeTextObjects(copies)

    # filter objects to only curves and textobjects
    copies = filterObjects(copies)
    
    # check curves for deviation from c-plane
    if checkCurvePosition(copies):
        
        copies = joinCurves(copies)
        simplify(copies)

        if checkCurveIntegrity(copies):

            # rs.UnselectAllObjects()

     
            
            # check curve dir
            if not setCurveDir(copies): print "checkAndExport aborted"; return

            # move to origin
            result = moveToOrigin(copies);

            if convert_for_biesse :
                biesse_layers = convertLayers(copies)

            # clamexdata = extractClamexOrientation(copies)
    
            if result:

                # export
                rs.SelectObjects(copies)

                redraw()

                filename = rs.SaveFileName ("Save", "Text Files (*.dxf)|*.dxf||")
                if filename: 
                
                    result = rs.Command('! _-Export "' + filename  +'" _Enter', False )
                    
                    filename_stripped, file_extension = os.path.splitext(filename)
                    
                    if export_clamex_txt and clamexdata:
                        
                        for line in clamexdata:
                            with open(filename_stripped + '.txt', 'a') as the_file:
                                the_file.write(line)
                    
                    if result: print 'exported succesfully'

    rs.DeleteObjects(copies)

    if len(biesse_layers)>0:
        for layer in biesse_layers:
            rs.PurgeLayer(layer)

    rs.EnableRedraw(True)


if __name__ == "__main__":
    main();
