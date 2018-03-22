

# with a textbox that can be used to define the text in a new text dot
from System.Windows.Forms import Form, DialogResult, Label, Button, TextBox, CheckBox, ComboBox, NumericUpDown
from System.Drawing import Point, Size
import rhinoscript.selection
import rhinoscript.geometry

import rhinoscriptsyntax as rs



# Our custom form class
class AnnotateForm(Form):
  # build all of the controls in the constructor
  def __init__(self, curveId):
    
    label_width = 70
    offset = 30
    index = 0
    
    # header
    self.Text = "add workpiece"
    
    #label
    index += 1

    crvlabel = Label(Text="Curve ID ", AutoSize=True)
    # self.Controls.Add(crvlabel)
    width = crvlabel.Right
    pt = Point(crvlabel.Left,crvlabel.Bottom + offset)
    # 
    #textInput
    labelstart = Label(Text="Workpiece Name", AutoSize=True)
    labelstart.Location = Point(5, offset* index)
    self.Controls.Add(labelstart)
    pt.X = labelstart.Right + offset
    inputstart = TextBox(Text="Start")
    inputstart.Location = pt
    self.Controls.Add(inputstart)
    if( inputstart.Right > width ):
      width = inputstart.Right
    self.m_inputstart = inputstart
    # 
    # index += 1
    # cb = CheckBox( AutoSize=True)
    # cb.Parent = self
    # cb.Location = Point(label_width, offset* index)
    # cb.Text = "Show Title"
    # cb.Checked = True

    
    

    index += 1
    
    labelstart = Label(Text="width:", AutoSize=True)
    labelstart.Location = Point(5, offset* index)
    self.Controls.Add(labelstart)

    sb = NumericUpDown( AutoSize=True, Location=Point(label_width, offset * index), Parent=self , DecimalPlaces = 2) 
    sb.Parent = self
    sb.Location = Point(label_width, offset* index)
    sb.DecimalPlaces  = 2
  
    index += 1
    labelstart = Label(Text="height:", AutoSize=True)
    labelstart.Location = Point(5, offset* index)
    self.Controls.Add(labelstart)
    sb = NumericUpDown( AutoSize=True, Location=Point(label_width, offset * index), Parent=self , DecimalPlaces = 2) 
    sb.Parent = self
    sb.Location = Point(label_width, offset* index)
    sb.DecimalPlaces  = 2

    index += 1
    labelstart = Label(Text="thickness:", AutoSize=True)
    labelstart.Location = Point(5, offset* index)
    self.Controls.Add(labelstart)
    sb = NumericUpDown( AutoSize=True, Location=Point(label_width, offset * index), Parent=self , DecimalPlaces = 2) 
    sb.Parent = self
    sb.Location = Point(label_width, offset* index)
    sb.DecimalPlaces  = 2
  
    
    index += 1
    cbb = ComboBox(Text="Material", Location=Point(label_width, offset * index), Parent=self)
    cbb.Items.AddRange(("VALxx",
            "VALBLK",
            "VALBLU",
            "VALGRY",
            "VALGRN",
            "VALYEL",
            "VALRED"))    
    
    self.cbb_operation = cbb      

    
    index += 1
    pt.X  = labelstart.Left
    pt.Y  = labelstart.Bottom + offset*index
    buttonApply = Button(Text="Apply", DialogResult=DialogResult.OK)
    buttonApply.Location = pt
    self.Controls.Add(buttonApply)
    pt.X = buttonApply.Right + offset
    buttonCancel = Button(Text="Cancel", DialogResult=DialogResult.Cancel)
    buttonCancel.Location = pt
    self.Controls.Add(buttonCancel)
    if( buttonCancel.Right > width ):
      width = buttonCancel.Right
    self.ClientSize = Size(width, buttonCancel.Bottom)
    self.AcceptButton = buttonApply
    self.CancelButton = buttonCancel
    
    


  def TextAtStart(self):
    return self.m_inputstart.Text

  def getLayerName(self):
    layername = ''
    layername += self.cbb_tool.Text
    return layername
    
    # main script
def main():

        form = AnnotateForm('test6575')
        if( form.ShowDialog() == DialogResult.OK ):
            #  this block of script is run if the user pressed the apply button
            text = form.TextAtStart()
            layername = form.getLayerName()
            rs.MessageBox(layername)

if __name__ == "__main__":
    main();
