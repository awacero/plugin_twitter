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

from eqelib import sqliteTweetDB
from eqelib import configFaceTweet as cfg

class Plugin(plugin.PluginBase):
    VERSION="0.2" 
    
    
    def __init__(self,app,generator,env,db,cursor):
        
        
        logging.info("Calling init")

        
        self.twt_acc=cfg.twitter_page
        self.hour_limit=cfg.LIMIT_HOURS       
        self.twt_prm=self.read_config_file(cfg.token_file)
        self.log_file=cfg.log_file
        if self.twt_prm == -1:
            logging.debug('Error while reading token file: %s' % (cfg.token_file))
            return(-1)
        
        
    def processEvent(self, ctx,path):
        
    #convert ctx to txt
    #CONNECT TO twt
    #publish in twt
    #store the ID in BD
        

        '''
        Create postDB according to configFaceTweet.py
        '''
        create_postDB = sqliteTweetDB.initDatabase()
        if create_postDB == -1:
            logging.debug("Could not create post DB. Exit")
            return(-1)
        
        
        
        d=self.ctx2dict(ctx,path)
        logging.info("##Created dict: %s" %d)
        
        '''
        Check event antiquity 
        '''
        if self.check_antiquity(d['date']) ==-1:
            logging.info("Event %s too old to publish" %d['evID'])
            return -1
        
        logging.info("Age of event %s ok. Publish " %(d['evID'])) 
        '''
        Check if event has been published
        '''     
        select="*"
        where="eventID='%s'" %d['evID']
        rows=sqliteTweetDB.getPost(select,where)
        
        for r in rows:
            if r['eventID']==d['evID'] and r['modo']==d['modo']:
                logging.info("Event already published")
                return 0
            else:
                logging.info("Event not found. Publish")
        
        
        '''
        Get API to twitter
        '''
        logging.info("##Connecting to twitter: %s" %self.twt_acc)
        twt_api=self.connect_twitter(self.twt_prm[self.twt_acc])
        
        '''
        Post to twitter
        '''
        logging.info("##Trying to post to twitter")
        tweetID=self.post_event(twt_api,d)
        
        '''
        Insert tweetID into DB  
        '''   
        ##call to insert into DB
        if tweetID==-1:
            "Error posting tweet"
            exit(-1)
        else:
            "Insert evID, twtID, status in DB"
            logging.info("##Insert twtID in DB")
            row_dct={'eventID':'%s' %d['evID'],'tweetID':'%s' %tweetID,'modo':'%s' %d['modo']}
            if sqliteTweetDB.savePost(row_dct)== 0:
                logging.info("Post info inserted in DB. %s, %s, %s" %(d['evID'],tweetID, d['modo']) )
            else:
                logging.info("Failed to insert tweet info in DB")
            return 0

        
            
    
    def check_antiquity(self, dt):
        """
        Check the age of a event
        Parameters:
            dt - datetime object
        """
        #date_event_EC = convert_date_UTC2local(eventDateString)
        date_check = datetime.now() - timedelta(hours=self.hour_limit)
        
        if date_check < dt:
            return 0
        else:
            return -1

       
        
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
        
        tweetPost="#TEST SISMO ID: %s %s %s TL Magnitude:%s Prof: %s km, %s,Latitud: %s Longitud:%s " \
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
        
    def delete_post(self, evID):
        """
        Delete post from twitter 
        """
        
        import logging
        logging.basicConfig(filename=self.log_file,format='%(asctime)s %(levelname)s %(message)s',level=logging.INFO)
        
        '''
        Get API of twitter
        '''
        logging.info("##Connecting to twitter: %s" %self.twt_acc)
        twt_api=self.connect_twitter(self.twt_prm[self.twt_acc])
        
        '''
        Check if event has been published and delete it
        '''     
        select="*"
        where="eventID='%s'" %evID
        rows=sqliteTweetDB.getPost(select,where)
        
        for r in rows:
            logging.info("Deleting post %s %s" %(r['eventID'],r['tweetID']))
            msg=twt_api.destroy_status(r['tweetID'])
            logging.info(msg)
        
        res=sqliteTweetDB.deletePost(evID)
        
        if res== 0:
            logging.info("Deleted from post.db")
        else:
            logging.info("Error deleting: %s" %res)
        
        
  

        