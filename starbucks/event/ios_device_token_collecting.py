#!/usr/bin/env python
# coding: utf-8

# In[3]:


import os
import oss2
import gzip
from itertools import islice
import json
import pandas as pd
import urllib3
import logging
import sys
from datetime import datetime


# In[138]:


logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

arguments=sys.argv
logging.info("Arguments length: " + str(len(arguments)) + ". Argurments: " + str(arguments))
if len(arguments) <= 1:
    print("usage: {} env. For example, {} test 20181220".format(arguments[0], arguments[0]))
    sys.exit(-1)

env=arguments[1]
if env == "prod":
    endpoint="oss-cn-shanghai-internal.aliyuncs.com"
    postProfileUrl="http://gateway.fnvalley.com/profile-service/2.0.0/extra_profile/saveIosDeviceTokenList"
    kafkaOssPathPrefix="kafka-bakcup/{}/event-prod"
elif env == "test":
    endpoint="oss-cn-shanghai-internal.aliyuncs.com"
    postProfileUrl="http://testgate.fnvalley.com/profile-service/2.0.0/extra_profile/saveIosDeviceTokenList"
    kafkaOssPathPrefix="kafka-bakcup-test/{}/event-test"
else:
    endpoint="oss-cn-shanghai.aliyuncs.com"
    postProfileUrl="http://testgate.fnvalley.com/profile-service/2.0.0/extra_profile/saveIosDeviceTokenList"
    kafkaOssPathPrefix="kafka-bakcup-test/{}/event-test"

if len(arguments) >= 3:
    date=arguments[2]
else:
    date=datetime.now().strftime("%Y%m%d")
    
accessKeyID="LTAItd3meVs30UzA"
accessKeySecret="mt9g18CLp18gqXcaWxLSZX4VqX1mH4"

internalBucket="internal-fnvalley"
ACCESS_TOKEN="4f55964d-d361-44fe-94d8-2f2eaedce16e"
loginIdDeviceTokenMap = {}

logging.info("Oss endpoint: " + endpoint)
logging.info("Collecting date: " + date)


# In[139]:


auth = oss2.Auth(accessKeyID, accessKeySecret)
bucket = oss2.Bucket(auth, 'http://' + endpoint, internalBucket)
http = urllib3.PoolManager()


# In[140]:


def checkAndAddDeviceToken(event):
    try:
        eventJson = json.loads(event)
        if eventJson.get("deviceToken") != None and eventJson.get("loginId") != None:
            loginIdDeviceTokenMap[eventJson.get("loginId")] = eventJson.get("deviceToken")
    except Exception as e:
        logging.info("Event: [" + event + "], Exeption: " + str(e))


# In[117]:


o = bucket.list_objects(prefix=kafkaOssPathPrefix.format(date))
for d in o.object_list:
    object_stream = bucket.get_object(d.key)
    data = gzip.decompress(object_stream.read())
    for event in data.decode('utf8').split("\r\n"):
        checkAndAddDeviceToken(event)


# In[120]:


logging.info("device token map: " + str(loginIdDeviceTokenMap))
if len(loginIdDeviceTokenMap) > 0:
    dataList = []
    for loginId in loginIdDeviceTokenMap: 
        data = {}
        data["loginId"] = loginId
        data["iosDeviceToken"] = loginIdDeviceTokenMap.get(loginId)
        if data["iosDeviceToken"] != "":
            dataList.append(data)
    response = http.request("POST", postProfileUrl, body = json.dumps(dataList), headers = {"Content-Type":"application/json", "Authorization": "Bearer " + ACCESS_TOKEN})
    logging.info("Response status: " + str(response.status))
    if response.status != 200:
        sys.exit(-1)

