'''

'''

import seiscomp3.Logging as logging

import eqelib.plugin as plugin
import eqelib.settings as settings

from datetime import datetime, timedelta
from eqelib import distancia

class Plugin(plugin.PluginBase):
    VERSION="0.2"
    
    def __init__(self,app,generator,env,db,cursor):
        
        pass
    
    def processEvent(self, ctx,path):
        
    #convert ctx to txt
    #CONNECT TO twt
    #publish in twt }
    
        self.ctx2dict(ctx)

    def ctx2dict(self,ctx):
        
        """
        receive a ctx object and return a dictionary of the event
        """
        d={}
        o=ctx['origin']
        d['evID']=ctx['ID']
        d['modo']=str(o.evaluationMode)
        dtime=o.time.value
        dtime=datetime.strptime(dtime[:19],"%Y-%m-%dT%H:%M:%S") -timedelta(hours=5)
        d['date']=dtime
        d['magV']="%.2f" %o.magnitude.magnitude.value
        d['dept']="%.2f" %o.depth.value
        d['dist']=distancia.closest_distance(o.latitude.value,o.longitude.value)
        d['lati']=o.latitude.value
        d['long']=o.longitude.value
        
        d['url']=distancia.create_google_url(d['date'],d['evID'])
        d['url']=str(distancia.short_url(d['url']))
        logging.info("##TWT txt %s" %d)
        
        
        
        
        