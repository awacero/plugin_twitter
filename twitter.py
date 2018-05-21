'''

'''

import seiscomp3.Logging as logging

import eqelib.plugin as plugin
import eqelib.settings as settings

from datetime import datetime, timedelta
from eqelib import distancia
#import twitterPublish
import json
import tweepy

class Plugin(plugin.PluginBase):
    VERSION="0.2"
    
    
    def __init__(self,app,generator,env,db,cursor):
        
        pass
    
    def processEvent(self, ctx,path):
        
    #convert ctx to txt
    #CONNECT TO twt
    #publish in twt
    #store the ID in BD
    
        twt_acc="AWACERO"
        twitterTokenFile='/home/seiscomp/git/twitter/twitter_account.json'
        twt_prm=self.read_config_file(twitterTokenFile)
        
        d=self.ctx2dict(ctx,path)
        logging.info("##Created dict: %s" %d)
                
        logging.info("##Connecting to twitter: %s" %twt_acc)
        twt_api=self.connect_twitter(twt_prm[twt_acc])
        
        logging.info("##Trying to post to twitter")
        tweetID=self.post_event(twt_api,d)

        logging.info("##Insert twtID in DB")
        ##call to insert into DB
        
        
    def ctx2dict(self,ctx,path):
        
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
        d['path']="%s/%s-map.png" %(path,d['evID'])
        return d

    def read_config_file(self,jsonFile):
        """
        read JSON files
        """
        try:
            with open(jsonFile) as json_data_files:
                return json.load(json_data_files)
        except Exception as e:
            logging.info("Error in read_config_file(): %s" %str(e))
            return -1
        
    def connect_twitter(self,tokenDict):
    
        try:
            auth = tweepy.OAuthHandler(tokenDict['api_key'],tokenDict['api_secret'])
            auth.set_access_token(tokenDict['access_token'],tokenDict['secret_token'])
            #redirect=auth.get_authorization_url()
            twitter_api = tweepy.API(auth)
            return twitter_api 
        except Exception as e:
            logging.info("Error trying to connect twitter: %s" %str(e))
            return -1


    def post_event(self,twitter_api,ev):
        """
        Posting event information in twitter
        """
        
        tweetPost="#SISMO ID: %s %s %s TL Magnitude:%s Prof: %s km, %s,Latitud: %s Longitud:%s " \
        %(ev['evID'],ev['modo'],ev['date'], ev['magV'],ev['dept'],ev['dist'],ev['lati'],ev['long'])

        try:
            logging.info(ev['path'])

            tweetID=twitter_api.update_with_media(ev['path'], tweetPost)
            #tweetID=twitter_api.update_status(tweetPost)
            logging.info("Posted event to twitter successfully")
            return tweetID.id
        
        except Exception as e:
            logging.info( "Error trying to post twitter: %s" %str(e))
            return -1
        


        