Name = 'ReadVolcalnoes'
Label = 'Show Volcano Locations'
FilterCategory = 'IRIS EMC'
Help = 'Read and display volcano locations.'

ExtraXml = '''\
<IntVectorProperty
    name="Data_Source"
    command="SetParameter"
    number_of_elements="1"
    initial_string="drop_down_menu"
    default_values="1">
    <EnumerationDomain name="enum">
          VOLCANO_DROP_DOWN
    </EnumerationDomain>
    <Documentation>
        Choose volcano locations service
    </Documentation>
</IntVectorProperty>
<IntVectorProperty
    name="Area"
    command="SetParameter"
    number_of_elements="1"
    initial_string="area_drop_down_menu"
    default_values="1">
    <EnumerationDomain name="enum">
          AREA_DROP_DOWN
    </EnumerationDomain>
    <Documentation>
        Choose the area to draw in.
    </Documentation>
</IntVectorProperty>
'''

NumberOfInputs = 0
OutputDataType = 'vtkPolyData'

Properties = dict(
    Data_Source       = 0,
    Area              = 1,
    Alternate_FileName   = "",
    Latitude_Begin     = '',
    Latitude_End       = '',
    Longitude_Begin    = '',
    Longitude_End      = ''
)

def RequestData():
    # R.0.2018.080
    import sys
    sys.path.insert(0, "EMC_SRC_PATH")
    import paraview.simple as simple
    import numpy as np
    import csv
    import os
    from vtk.util import numpy_support as nps
    import IrisEMC_Paraview_Lib as lib
    import urlparse

    Label = ''

    pts = vtk.vtkPoints()

    # make sure we have input files
    query = lib.volcanoLocationsQuery
    if len(Alternate_FileName) <= 0:
        volcanoFile = lib.query2fileName(query)
        query = '?'.join([lib.volcanoLocationsKeys[Data_Source],query])
        fileFound,address,source = lib.findFile(volcanoFile,loc='EMC_VOLCANOES_PATH',query=query)
        Label = ' '.join([lib.volcanoLocationsValues[Data_Source].strip(),'from',urlparse.urlparse(lib.volcanoLocationsKeys[Data_Source]).netloc.strip()])
    else:
       fileFound,address,source = lib.findFile(Alternate_FileName,loc='EMC_VOLCANOES_PATH')


    if not fileFound:
        raise Exception('volcano file "'+address+'" not found! Please provide the full path or UR for the file. Aborting.')
    (params,lines) = lib.readGcsv(address)

    Latitude_Begin,Latitude_End,Longitude_Begin,Longitude_End = lib.getArea(Area,Latitude_Begin,Latitude_End,Longitude_Begin,Longitude_End)
    Label2 = " - %s (lat:%0.1f,%0.1f, lon:%0.1f,%0.1f)"%(lib.areaValues[Area],Latitude_Begin,Latitude_End,Longitude_Begin,Longitude_End)

    pdo         = self.GetOutput() # vtkPoints
    count       = 0
    latIndex    = 0
    lonIndex    = 1

    column_keys = lib.columnKeys
    for key in lib.columnKeys.keys():
        if key in params.keys():
            column_keys[key] = params[key]

    delimiter   = params['delimiter'].strip()
    
    origin = None
    if 'source' in params:
        origin = params['source']
        if len (Label.strip()) <= 0:
            Label = origin
    header = lines[0].strip()
    fields = header.split(delimiter)
    for i in range(len(fields)):
          if fields[i].strip().lower() == column_keys['longitude_column'].lower():
             lonIndex = i
          elif fields[i].strip().lower() == column_keys['latitude_column'].lower():
             latIndex = i
          elif fields[i].strip().lower() == column_keys['elevation_column'].lower():
             elevIndex = i
    for i in range(1,len(lines)):
       line = lines[i].strip()
       values = line.strip().split(params['delimiter'].strip())
       try:
          lat   =  float(values[latIndex])
          lon   =  float(values[lonIndex])
       except:
          continue
       if len(values[elevIndex].strip()) <= 0:
          depth = 0.0
       else:
         try:
            depth = -1*float(values[elevIndex])/1000.0
         except:
            continue
       if lat>= Latitude_Begin and lat <= Latitude_End and lon >= Longitude_Begin and lon <= Longitude_End:
          x,y,z = lib.llz2xyz(lat,lon,depth)
          pts.InsertNextPoint(x,y,z)
    pdo.SetPoints(pts)

    done = False
    simple.RenameSource(' '.join(['Volcano locations:',Label.strip(),Label2.strip()]))

    view = simple.GetActiveView()

    # store metadata
    fieldData = pdo.GetFieldData()
    fieldData.AllocateArrays(3) # number of fields

    data = vtk.vtkFloatArray()
    data.SetName('Latitude\nRange (deg)')
    data.InsertNextValue(Latitude_Begin)
    data.InsertNextValue(Latitude_End)
    fieldData.AddArray(data)

    data = vtk.vtkFloatArray()
    data.SetName('Longitude\nRange (deg)')
    data.InsertNextValue(Longitude_Begin)
    data.InsertNextValue(Longitude_End)
    fieldData.AddArray(data)

    data = vtk.vtkStringArray()
    data.SetName('Source')
    if origin is not None:
       data.InsertNextValue(origin)

    data.InsertNextValue(source)
    fieldData.AddArray(data)

    pdo.SetFieldData(fieldData)

def RequestInformation():
    from paraview import util
    sys.path.insert(0, "EMC_SRC_PATH")
    import IrisEMC_Paraview_Lib as lib
    query = lib.volcanoLocationsQuery
    if len(Alternate_FileName) <= 0:
        volcanoFile = lib.query2fileName(query)
        query = '?'.join([lib.volcanoLocationsKeys[Data_Source],query])
        fileFound,address,source = lib.findFile(volcanoFile,loc='EMC_VOLCANOES_PATH',query=query)
    else:
       fileFound,address,source = lib.findFile(Alternate_FileName,loc='EMC_VOLCANOES_PATH')

    if not fileFound:
        raise Exception('volcano file "'+address+'" not found! Please provide the full path or UR for the file. Aborting.')
    (params,lines) = lib.readGcsv(address)
    num = len(lines)
    # ABSOLUTELY NECESSARY FOR THE READER TO WORK:
    util.SetOutputWholeExtent(self, [0,num-1, 0,num-1, 0,num-1])
