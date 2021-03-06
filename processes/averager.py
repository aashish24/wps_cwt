from pywps.Process import WPSProcess
import os
import json
import cdms2
import cdutil
cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)
import random
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'output'))
from tools import ESGFCWTProcess

class Process(ESGFCWTProcess):
    def __init__(self):
        """Process initialization"""
        WPSProcess.__init__(self, identifier=os.path.split(__file__)[-1].split('.')[0], title='averager', version=0.1, abstract='Average a variable over a (many) dimension', storeSupported='true', statusSupported='true')
        self.domain = self.addComplexInput(identifier='domain', title='domain over which to average', formats=[{'mimeType': 'text/json',
          'encoding': 'utf-8',
          'schema': None}])
        self.download = self.addLiteralInput(identifier='download', type=bool, title='download output', default=False)
        self.dataIn = self.addComplexInput(identifier='variable', title='variable to average', formats=[{'mimeType': 'text/json'}], minOccurs=1, maxOccurs=1)
        self.average = self.addComplexOutput(identifier='average', title='averaged variable', formats=[{'mimeType': 'text/json'}])

    def execute(self):
        dataIn=self.loadData()[0]
        domain = self.loadDomain()
        cdms2keyargs = self.domain2cdms(domain)
        f=self.loadFileFromURL(dataIn["url"])
        data = f(dataIn["id"],**cdms2keyargs)
        dims = "".join(["(%s)" % x for x in cdms2keyargs.keys()])
        data = cdutil.averager(data,axis=dims)
        data.id=dataIn["id"]
        self.saveVariable(data,self.average,"json")
        return
