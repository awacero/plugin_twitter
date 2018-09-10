
import sys,os
HOME=os.getenv("HOME")
sys.path.append("%s/plugins_python/twitter" %HOME)



import seiscomp3.Logging as logging
import eqelib.plugin as plugin
import eqelib.settings as settings

from datetime import datetime, timedelta
import json
import tweepy
import sqliteTweetDB
#from eqelib import sqliteTweetDB


from eqelib import configFaceTweet as cfg
from eqelib import distancia

class Plugin(plugin.PluginBase):
    VERSION="0.2" 
    
    
    def __init__(self,app,generator,env,db,cursor):
        
        
        logging.info("Calling init")

        
        self.twt_acc=cfg.twitter_page
        self.hour_limit=cfg.LIMIT_HOURS       
        self.twt_prm=self.read_config_file(cfg.tw_token_file)
        self.log_file=cfg.tw_log_file
        if self.twt_prm == False:
            logging.debug('Error while reading token file: %s' % (cfg.tw_token_file))
            return False
        
        
    def processEvent(self, ctx,path):        
        
        """         Process the event         """
        logging.info("###Start post in Twitter")
    
        
        """        Create postDB according to configFaceTweet.py         """
        create_postDB = sqliteTweetDB.initDatabase()
        if create_postDB == -1:
            logging.debug("Could not create post DB. Exit")
            return False
        
        
    	"""     	Create the dictionary from ctx """        
        d=self.ctx2dict(ctx,path)
        logging.info("Created dict: %s" %d)
        
        """         Check event antiquity """
        if self.check_antiquity(d['date']) == False:
            logging.info("Event %s too old to publish" %d['evID'])
            return False
        
        logging.info("Age of event %s ok. Publish " %(d['evID'])) 
        
        """         Check if event has been published     """
             
        select="*"
        where="eventID='%s'" %d['evID']
        rows=sqliteTweetDB.getPost(select,where)
        
        for r in rows:
            if r['eventID']==d['evID'] and r['modo']==d['modo']:
                logging.info("Event already published")
                return True
            else:
                logging.info("Event not found. Continue to publish")
                #return True
        
        """         Get API to twitter         """
        logging.info("Connecting to twitter: %s" %self.twt_acc)
        twt_api=self.connect_twitter(self.twt_prm[self.twt_acc])
        
        """         Post to twitter         """
        logging.info("Trying to post to twitter")
        tweetID=self.post_event(twt_api,d)
        
        """         Insert tweetID into DB         """   
        ##call to insert into DB
        if tweetID==False:
            logging.info("Error posting tweet")
            return False
        else:
            "Insert evID, twtID, status in DB"
            logging.info("##Insert twtID in DB")
            row_dct={'eventID':'%s' %d['evID'],'tweetID':'%s' %tweetID,'modo':'%s' %d['modo']}
            if sqliteTweetDB.savePost(row_dct)== 0:
                logging.info("Post info inserted in DB. %s, %s, %s" %(d['evID'],tweetID, d['modo']) )
                return True
            else:
                logging.info("Failed to insert tweet info in DB")
            return False

            
    
    def check_antiquity(self, dt):
        """ Check the age of a event 
                Parameters:
                dt - datetime object
        """
        #date_event_EC = convert_date_UTC2local(eventDateString)
        date_check = datetime.now() - timedelta(hours=self.hour_limit)
        
        if date_check < dt:
            return True
        else:
            return False

    def status(self,stat):
        if stat == 'automatic':
            stat = 'Preliminar'
        elif stat == 'manual':
            stat = 'Revisado'
        else:
            stat = '.'
        return stat
    
    
        
    def ctx2dict(self,ctx,path):
        
        """         receive a ctx object and return a dictionary of the event         """
        d={}
        o=ctx['origin']
        d['evID']=ctx['ID']
        d['modo']=self.status(str(o.evaluationMode))
        dtime=o.time.value
        dtime=datetime.strptime(dtime[:19],"%Y-%m-%dT%H:%M:%S") -timedelta(hours=5)
        d['date']=dtime
        d['magV']="%.2f" %o.magnitude.magnitude.value
        d['dept']="%.2f" %o.depth.value
        d['dist']=distancia.closest_distance(o.latitude.value,o.longitude.value)
        d['lati']="%.4f" %o.latitude.value
        d['long']="%.4f" %o.longitude.value
        d['url']=distancia.create_google_url(d['date'],d['evID'])
        d['url']=str(distancia.short_url(d['url']))       
        d['path']="%s/%s-map.png" %(path,d['evID'])
        return d

    def read_config_file(self,jsonFile):
        """         read JSON files         """
        try:
            with open(jsonFile) as json_data_files:
                return json.load(json_data_files)
        except Exception as e:
            logging.info("Error in read_config_file(): %s" %str(e))
            return False
        
    def connect_twitter(self,tokenDict):
    
        try:
            auth = tweepy.OAuthHandler(tokenDict['api_key'],tokenDict['api_secret'])
            auth.set_access_token(tokenDict['access_token'],tokenDict['secret_token'])
            #redirect=auth.get_authorization_url()
            twitter_api = tweepy.API(auth)
            return twitter_api 
        except Exception as e:
            logging.info("Error trying to connect twitter: %s" %str(e))
            return False


    def post_event(self,twitter_api,ev):
        """         Posting event information in twitter         """
        
        tweetPost="#TEST SISMO ID: %s %s %s TL Magnitud:%s Profundidad: %s km, %s,Latitud: %s Longitud:%s Sintio este sismo? Reportelo! en %s"\
        %(ev['evID'],ev['modo'],ev['date'], ev['magV'],ev['dept'],ev['dist'],ev['lati'],ev['long'],ev['url'])

        try:
            logging.info(ev['path'])

            tweetID=twitter_api.update_with_media(ev['path'], tweetPost)
            #tweetID=twitter_api.update_status(tweetPost)
            logging.info("Posted event to twitter successfully")
            return tweetID.id
        
        except Exception as e:
            logging.info( "Error trying to post twitter: %s" %str(e))
            return False
        
    def delete_post(self, evID):
        """         Delete post from twitter         """
        
        import logging
        logging.basicConfig(filename=self.log_file,format='%(asctime)s %(levelname)s %(message)s',level=logging.INFO)
        
        """         Get API of twitter         """
        logging.info("##Connecting to twitter: %s" %self.twt_acc)
        twt_api=self.connect_twitter(self.twt_prm[self.twt_acc])
        
        """         Check if event has been published and delete it         """     
        select="*"
        where="eventID='%s'" %evID
        rows=sqliteTweetDB.getPost(select,where)
        
        for r in rows:
            try:
                
                logging.info("Deleting post %s %s" %(r['eventID'],r['tweetID']))
                msg=twt_api.destroy_status(r['tweetID'])
                logging.debug(msg)
                
                res=sqliteTweetDB.deletePost(evID)
        
                if res== True:
                    logging.info("Deleted from post.db")
                    return True
                else:
                    logging.info("Error deleting: %s from post.db" %res)
                    return False
                
                
            except Exception as e:
                logging.info("Error in delete_post(): %s" %(str(e)))
                return False
            

        
        
  

        
