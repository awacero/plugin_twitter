'''
Created on Oct 31, 2017

@author: wacero
'''

workspace   =   "/home/seiscomp/workspace/pluginTwitter"

twitter_account_file  =   "%s/%s" %(workspace,"twitter_account.json")

log_file    =   "%s/%s" %(workspace,"twitter_plugin.log")

dbname      =   "%s/%s" %(workspace,"twitter_post.db")

dbtable     =   "twitter_post"

LIMIT_HOURS =   20000

DATE_FORMAT =   '%Y/%m/%d %H:%M:%S'

local_zone  =   'America/Guayaquil'

account =   "IGEPNSwift"