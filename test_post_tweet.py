import tweepy
import json 
from eqelib import configFaceTweet as cfg
from datetime import datetime


def read_config_file(jsonFile):
    """         read JSON files         """
    try:
        with open(jsonFile) as json_data_files:
            return json.load(json_data_files)
    except Exception as e:
        print("Error in read_config_file(): %s" %str(e))
        return False



token_prm=read_config_file(cfg.tw_token_file)
twitter_account = cfg.twitter_page
token_dict = token_prm[twitter_account]

file_path = "./image_test.png"
auth = tweepy.OAuthHandler(token_dict['api_key'],token_dict['api_secret'])
auth.set_access_token(token_dict['access_token'],token_dict['secret_token'])
twitter_api = tweepy.API(auth)

#twitter_api.update_status("Test message: %s " %datetime.now()  )
twitter_api.update_with_media( file_path, "Test message: %s " %datetime.now()  )

print(datetime.now())

