import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import math
import time
import re

# '_-runPythonScript "E:/rhinoscript/extractRotation2.py"

    
def vecLen(a):
    return math.sqrt(sum( [ math.pow(a[i],2) for i in range(len(a))] ))    
    
def calcAngle(vec1, vec2):
    dotpr = sum( [vec1[i]*vec2[i] for i in range(len(vec2))] )
    theta = math.acos( dotpr / (vecLen(vec1) * vecLen(vec2) ) )
    
    if(vec1[1]<vec2[1]):
        theta-=2* math.pi
    
    return theta   
    
def main():


    print 'test' 
    
    objs = rs.GetObjects()
    vec_x = [10,0,0]

    # restore viewport Cplane
    p1 = rs.WorldXYPlane()
    rs.ViewCPlane(None, p1)    
    
    for obj in objs:
       
            
        
        if rs.IsBlockInstance(obj) and rs.BlockInstanceName(strObject):

        xform1 = rs.BlockInstanceXform(obj)
        crv = rs.AddCurve([ [0,0,0], [0,300,0] ])
        xfrom1_inv = rs.TransformObject( crv, (xform1) )

        rs.SelectObject(crv)
     
     
        vec1 = rs.CurveEndPoint(crv) - rs.CurveStartPoint(crv)
        print vec1, math.degrees(calcAngle(vec1, vec_x))
        
        

         
    
if __name__ == "__main__":
    main();