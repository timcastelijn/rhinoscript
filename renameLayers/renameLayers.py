import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import math
import re
import time
import os


#add to rhino as an alias
if not rs.IsAlias("TNM_renameLayers"):
    rs.AddAlias("TNM_renameLayers",  "'_-runPythonScript \"%s\"" % __file__ )
    print 'addAlias'
else:
    print 'alias could not be added'

layers = rs.LayerIds()
for layer_id in layers: 

    if rs.IsLayer(layer_id):
    
        old_name = rs.LayerName(layer_id, False)

        if (re.search('0.0.0', old_name ) ):
            
            new_name = old_name.replace('0.0.0', '0.0.160.0')
            
            rs.RenameLayer(old_name, new_name)
    else:
        print layer_id

