'''
Created on Oct 31, 2017

@author: wacero
'''

import sys
import sqliteTwitterDB
sys.path.append('/home/seiscomp/seiscomp3/share/eqevents/python/')

from datetime import datetime,timedelta
import pytz
import sqliteDbLib
import tweepy
import json
import logging
import configuracionTwitter



logging.basicConfig(filename=configuracionTwitter.log_file, level=logging.DEBUG)

twitter_account_file       =  configuracionTwitter.twitter_account_file
LIMIT_HOURS      =  configuracionTwitter.LIMIT_HOURS
DATE_FORMAT      =  configuracionTwitter.DATE_FORMAT
local_time_zone  =  pytz.timezone(configuracionTwitter.local_zone)
account          =  configuracionTwitter.account


def get_event_fromDB(eventID):
    try:
        eventos = sqliteDbLib.outputDB(where="eventID='%s'" % (eventID))
        if eventos:
            return eventos[0]
        else:
            return -1
    except Exception as e:
        logging.debug("Error get_event_fromDB(): %s. Error: %s" % (eventID, str(e)))
        return -1

def convert_date_UTC2local(dateUTCstring):
    dateUTC = datetime.strptime(dateUTCstring, DATE_FORMAT)
    dateEC = dateUTC.replace(tzinfo=pytz.utc).astimezone(local_time_zone)
    return dateEC.strftime(DATE_FORMAT)


def check_antiquity(eventDateString):
    date_event_EC = convert_date_UTC2local(eventDateString)
    date_check = datetime.now() - timedelta(hours=LIMIT_HOURS)
    if date_check < datetime.strptime(date_event_EC, DATE_FORMAT):
        return 0
    else:
        return -1
    
def read_config_file(json_file):
    try:
        with open(json_file) as json_data_files:
            return json.load(json_data_files)
    except Exception as e:
        logging.debug("Error readConfigFile(): %s" % str(e))
        return -1



def connect_twitter(tokenDict):

    try:
        auth = tweepy.OAuthHandler(tokenDict['api_key'],tokenDict['api_secret'])
        auth.set_access_token(tokenDict['access_token'],tokenDict['secret_token'])
        #redirect=auth.get_authorization_url()
        twitter_api = tweepy.API(auth)
        return twitter_api 
    except Exception as e:
        logging.info("Error trying to connect twitter: %s" %str(e))
        return -1



def twitter_plugin(evID):
    '''
    Read token file and set token global variables
    '''
    token   =   read_config_file(twitter_account_file)
    if token == -1:
        logging.debug('Error while reading token file: %s' % (twitter_account_file))
        return('Error while reading token file: %s' % (twitter_account_file))

    else:
        
        global twitter_api
        twitter_api = connect_twitter(token[account])
        
        if twitter_api == -1:
            logging.info("Error accessing twitter account")
            return("Error on connect_twitter")
        
        '''
        Check if event exists in events.db and set dictionary
        '''
        eventDict=get_event_fromDB(evID)
        if eventDict == -1:
            logging.debug("Error getting event dictionary")
            return("Error getting event dictionary")
        
        '''
        Check antiquity of event according to LIMIT_HOURS
        '''
        antiquity = check_antiquity(eventDict['timestampSec'])
        if antiquity == -1:
            logging.debug("Event too old to publish")
            return("Event too old to publish")       
            
        
        '''
        Create postDB according to configuracionTwitter.py
        '''
        create_postDB = sqliteTwitterDB.initDatabase()
        if create_postDB == -1:
            logging.debug("Could not create post DB. Exit")
            return("Could not create post DB. Exit")

        '''
        
        '''
    
twitter_plugin('igepn2017brcq')


