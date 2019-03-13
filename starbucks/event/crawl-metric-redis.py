#!/usr/bin/env python
# coding: utf-8

# In[32]:


import urllib.request
import xml.etree.ElementTree as ET
import datetime
import time
import json
import redis


# In[33]:


INFLUXDB_HOST="10.10.0.214:8086"
#INFLUXDB_HOST="10.10.0.208:8086"
INFLUXDB_DATABASE="cityzone"
ACCESS_TOKEN="4f55964d-d361-44fe-94d8-2f2eaedce16e"
DATE_TIME=int(time.time()) * 1000000000
TIMEOUT=10
postUrl = "http://{}/write?db={}".format(INFLUXDB_HOST, INFLUXDB_DATABASE)


# In[34]:


pool = redis.ConnectionPool(host='testgate.zan-qian.com', port=6379, password="640f9791f9d73033UG", decode_responses=True)
r = redis.Redis(connection_pool=pool)
info = r.info()


# In[35]:


def sendMetric(info, name):
    value = info.get(name)
    data = "redisInfo,name={} value={} {}".format(name, value, DATE_TIME)
    urllib.request.urlopen(url = postUrl, data = data.encode('utf-8'))


# In[38]:


def sendDbMetric(info):
    dbName = "db0"
    value = info.get(dbName)
    for key in value:
        data = "redisInfo,name={} value={} {}".format(dbName + "." + key, value[key], DATE_TIME)
        urllib.request.urlopen(url = postUrl, data = data.encode('utf-8'))


# In[39]:


names = ["connected_clients","blocked_clients","used_memory","used_memory_rss","used_memory_peak","used_memory_lua","total_connections_received","total_commands_processed","instantaneous_ops_per_sec","total_net_input_bytes","total_net_output_bytes","keyspace_hits","keyspace_misses","used_cpu_sys","used_cpu_user"]
for name in names:
    sendMetric(info, name)

sendDbMetric(info)


# In[40]:





# In[ ]:




