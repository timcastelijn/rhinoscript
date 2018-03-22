

# with a textbox that can be used to define the text in a new text dot
from System.Windows.Forms import Form, DialogResult, Label, Button, TextBox, CheckBox, ComboBox, NumericUpDown
from System.Drawing import Point, Size
import rhinoscript.selection
import rhinoscript.geometry

import rhinoscriptsyntax as rs

import os
from subprocess import check_output


# Our custom form class
class AnnotateForm(Form):
  # build all of the controls in the constructor
  def __init__(self, tools):
    
    label_width = 30
    offset = 30
    index = 0
    
    # header
    self.Text = "Add layer"
    width = 400
    
    #label

    
    #textInput
    # labelstart = Label(Text="Text at start", AutoSize=True)
    # labelstart.Location = Point(label_width, offset* index)
    # self.Controls.Add(labelstart)
    # pt.X = labelstart.Right + offset
    # inputstart = TextBox(Text="Start")
    # inputstart.Location = pt
    # self.Controls.Add(inputstart)
    # if( inputstart.Right > width ):
      # width = inputstart.Right
    # self.m_inputstart = inputstart

    # TOOL SELECTON
    index += 1
    cbb = ComboBox(Text="Outer contour", Location=Point(label_width, offset * index), Parent=self, Width=200,)
    cbb.Items.AddRange(("Inner contour",
            "Outer contour",
            "Pocket",
            "Engrave",
            "Drill",
            "Saw X",
            "Saw Y",
            "Clamex verticaal",
            "Clamex horizontaal"))    
    cbb.TextChanged += self.updateLabelLayername
    self.cbb_operation = cbb
    
    # TOOL SELECTON
    index += 1
    cbb = ComboBox(Text=tools[0], Location=Point(label_width, offset * index), Parent=self, Width=200)
    cbb.Items.AddRange(tools)
    cbb.TextChanged += self.updateLabelLayername
    
    self.cbb_tool = cbb

            
    index += 1
    sb = NumericUpDown( AutoSize=True, Location=Point(label_width, offset * index), Parent=self , DecimalPlaces = 2)
    sb.ValueChanged += self.updateLabelLayername

    self.sb_height = sb     

    index += 1
    cb = CheckBox(Text = "use depth from top of workpiece",  AutoSize=True, Location = Point(label_width, offset* index), Parent=self)
    cb.Checked = False
    cb.CheckedChanged += self.updateLabelLayername
    
    self.cb_depth = cb 
    
    index += 1
    la = Label( Text="<layername>", Location=Point(label_width, offset * index), Parent=self, AutoSize=True) 
    self.la_layername = la
            
    index += 1
    pt = Point(label_width, offset * index)

    
    
    buttonApply = Button(Text="Apply", DialogResult=DialogResult.OK)
    buttonApply.Location = pt
    self.Controls.Add(buttonApply)
    pt.X = buttonApply.Right + offset
    buttonCancel = Button(Text="Cancel", DialogResult=DialogResult.Cancel)
    buttonCancel.Location = pt
    self.Controls.Add(buttonCancel)
    if( buttonCancel.Right > width ):
      width = buttonCancel.Right
    self.ClientSize = Size(width, buttonCancel.Bottom + 10)
    self.AcceptButton = buttonApply
    self.CancelButton = buttonCancel
    
  def updateLabelLayername(self, *args): 
    # print args
    self.la_layername.Text = self.getLayerName()  


  def getLayerName(self):
    
    if ("Clamex horizontaal" in self.cbb_operation.Text) or ('6.0.000.1' in self.cbb_tool.Text)  :
        self.cbb_operation.Text = "Clamex horizontaal"
        self.cbb_tool.Text = '6.0.000.1 -'
        
    if ("Clamex verticaal" in self.cbb_operation.Text) or ('6.0.000.1' in self.cbb_tool.Text)  :
        self.cbb_operation.Text = "Clamex verticaal"
        self.cbb_tool.Text = '6.1.000.1 -'    
        
    if ("Saw X" in self.cbb_operation.Text) or ("Saw Y" in self.cbb_operation.Text)  :
        self.cbb_operation.Text = "Clamex verticaal"
        self.cbb_tool.Text = '7.0.000.1 -'
        
    if( "Drill" in self.cbb_operation.Text and self.cbb_tool.Text[:2] != '5.'):
        rs.MessageBox('Please select a Drill')
        return ""
        
  
  
    if self.cb_depth.Checked:
        layername = '{} {} d{}'.format(self.cbb_tool.Text, self.cbb_operation.Text, self.sb_height.Value)
    else:
        layername = '{} {} +{}'.format(self.cbb_tool.Text, self.cbb_operation.Text, self.sb_height.Value)
        
    return layername
    
    # main script
def main():

        try: 
            check_output("python E:\python\gsheets\quickstart.py", shell=True)
            print 'tooltable updated'
        except:
            print 'NOT updated' 

        tools = []
        
        with open('output.txt') as fp:
            # read header
            line = fp.readline()
            # read first line
            line = fp.readline()
            cnt = 1
            while line:
                list = line.split(',')
                # print cnt, list[1]
                    
                tools.append( list[0] + " - " + list[1] )
        
                line = fp.readline()
                cnt += 1    
        
        tools = tuple(tools)
        
        form = AnnotateForm(tools)
        if( form.ShowDialog() == DialogResult.OK ):
            #  this block of script is run if the user pressed the apply button
            layername = form.getLayerName()
            
            if layername != '':
                rs.AddLayer(name=layername, parent = "CNC")
                rs.MessageBox(layername)
            

if __name__ == "__main__":
    main();
