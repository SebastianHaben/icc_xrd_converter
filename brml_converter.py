"""Plugin for specio library to read .BRML files"""

# Copyright (c) 2019
# Authors: Sebastian Haben
# Licence: MIT

import tempfile
import shutil
from zipfile import ZipFile

import numpy as np
import xml.etree.ElementTree as et

from specio import formats
from specio.core import Format
from specio.core.util import Spectrum

class BRML(Format):
    """Plugin to read BRML files which is used by Bruker X-Ray
    diffractometers. Information about the BRML can be found here [1]."""

    def can_read(self, request):
        """Checks if file can be read.

            Parameters:
            ----------
            request : Request
                Request object of the to be read file.

            Returns:
            --------
            bool
            """
        if request.filename.lower().endswith(self.extensions):
            return True
        return False

    class Reader(Format.Reader):
        """Reader Class to read .BRML files"""
        def _read_brml(self, brml_file):
            """Extracts diffraction data and metadata from file

                Parameters:
                -----------
                brml_file : file
                    The file containg the data.

                Returns:
                --------
                specio.Spectrum object"""
            # Create temporary directory to unzip the file
            with tempfile.TemporaryDirectory() as tmpdir:
                # Unzip File
                zip_file = ZipFile(brml_file)
                # Extract .xml file containg the data
                raw_data = zip_file.extract('Experiment0/RawData0.xml')

                # Creating tree and root to interact with .xml file
                tree = et.parse(raw_data)
                root = tree.getroot()

                # Extracting Metadata
                start = root.find('./TimeStampStarted').text
                end = root.find('./TimeStampFinished').text

                tps = float(root.find('.//TimePerStep').text)
                increment = float(root.find('.//ScanAxisInfo[@AxisName="TwoTheta"]/Increment').text)

                start_point = float(root.find('.//ScanAxisInfo[@AxisName="TwoTheta"]/Start').text)
                end_point = float(root.find('.//ScanAxisInfo[@AxisName="TwoTheta"]/Stop').text)

                sample_name = root.find('.//InfoItem[@Name="SampleName"]').attrib['Value']

                detector = root.find('.//Detectors/InfoData').attrib['VisibleName']
                try:
                    opening = float(root.find('.//Detectors/InfoData/AngularOpening').attrib['Value'])
                except AttributeError:
                    opening = ""
                tube = root.find('.//TubeMaterial').text
                tube_mat = root.find('.//TubeMaterial').text

                
                # Create metadata dictionary
                meta = {'SampleName':sample_name,'StartTime':start,
                        'EndTime':end,'StartPoint': start_point,
                        'EndPoint': end_point,'StepSize':increment,
                        'TimePerStep': tps, 'Detector': detector,
                        'DetectorOpening':opening,'Tube':tube,
                        'TubeMaterial':tube_mat}

                # Extract Data points to build diffractogram
                # Check if several Data ranges are available
                if len(root.findall('.//DataRoute')) > 1:
                    data = root.findall('.//DataRoute[@RouteFlag="Final"]/Datum')
                else:
                    data = root.findall('.//DataRoute/Datum')
                data_length = len(data[0].text.split(','))
                data_arr = arr = np.zeros([len(data),data_length])

                for i in range(0,len(data)):
                    data_arr[i,:] = data[i].text.split(',')

                intensity = data_arr[:,4]
                twotheta = data_arr[:,2]
                shutil.rmtree('./Experiment0')
            return Spectrum(intensity, twotheta, meta)
            
        def _open(self):
            #Open the reader
            self._fp = self._request.get_file()
            self._data = self._read_brml(self._fp)

        def _close(self):
            pass

# Importing BRML reader into specio
format = BRML('BRML', 'Bruker .brml file', '.brml')
formats.add_format(format)
        
