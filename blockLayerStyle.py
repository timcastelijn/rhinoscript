import Rhino
import scriptcontext
import rhinoscriptsyntax as rs
from scriptcontext import doc

def InstanceDefinitionObjects():

    names = rs.BlockNames(True)
    if names:
        for block_name in names:

            instanceDefinition = doc.InstanceDefinitions.Find(block_name, True)
            if not instanceDefinition:
                print "{0} block does not exist".format(block_name)
                return
            else:
                # set the layer status
                instanceDefinition.LayerStyle = 1
                print instanceDefinition.LayerStyle



if __name__=="__main__":
    InstanceDefinitionObjects()
    
    
    