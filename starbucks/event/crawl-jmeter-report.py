#!/usr/bin/env python
# coding: utf-8

# In[1]:


import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import json
import html.parser
import re


# In[2]:


JMETER_REPORT_HOST="10.10.0.221"
#INFLUXDB_HOST="10.10.0.208:8086"
INFLUXDB_HOST="10.10.0.214:8086"
INFLUXDB_DATABASE="cityzone"
MEASUREMENT_NAME="jmeterreport"
DATE_STR=datetime.now().strftime("%Y%m%d")
TIMEOUT=10


# In[3]:


def sendItemData(service, nanoDateTime, itemData):
    if len(itemData) == 13:
        label = itemData[0].replace(" ", "\\ ")
        sample = itemData[1]
        error = itemData[2]
        errorRate = itemData[3]
        avg = itemData[4]
        min = itemData[5]
        max = itemData[6]
        th90 = itemData[7]
        th95 = itemData[8]
        th99 = itemData[9]
        throughput = itemData[10]
        received = itemData[11]
        sent = itemData[12]
        fieldData = "sample={},error={},errorRate={},avg={},min={},max={},90th={},95th={},99th={},throughput={},received={},sent={}".format(sample, error, errorRate,avg,min,max,th90,th95,th99,throughput,received,sent)
        data = "{},service={},label={} {} {}".format(MEASUREMENT_NAME,service,label,fieldData,nanoDateTime)
        urllib.request.urlopen(url = "http://{}/write?db={}".format(INFLUXDB_HOST, INFLUXDB_DATABASE), data = data.encode('utf-8'))


# In[4]:


def crawl_jmeter_data(service):
    print("Service is " + service)
    url = "http://{}/{}/{}".format(JMETER_REPORT_HOST, DATE_STR, service)
    response = urllib.request.urlopen(url, timeout=TIMEOUT)
    html = response.readlines()
    startDate = ""
    for line in html:
        if startDate == "get": 
            startDate = str(line)
            match = re.search(".*<td>\"(.+)\"</td>.*", startDate)
            if match:
                startDate = match.group(1)
        if "Start Time" in str(line):
            startDate = "get"        
    date = datetime.strptime(startDate, "%m/%d/%y %I:%M %p")
    print(date)
    nano_time = date.strftime("%s000000000")
    
    dataUrl = "http://{}/{}/{}/content/js/dashboard.js".format(JMETER_REPORT_HOST, DATE_STR, service)
    response = urllib.request.urlopen(dataUrl, timeout=TIMEOUT)
    html = response.readlines()
    for line in html:
        if "statisticsTable" in str(line):
            contentLine = str(line, "utf-8")
            match = re.search(".*statisticsTable\"\), (\{.+\}), function.*", contentLine)
            if match:
                statisticsJson = json.loads(match.group(1))
                sendItemData(service, nano_time, statisticsJson["overall"]["data"])
                for item in statisticsJson["items"]:
                    sendItemData(service, nano_time, item["data"])


# In[5]:


crawl_jmeter_data("task-service")
crawl_jmeter_data("uaa-service")
crawl_jmeter_data("asset-service")
crawl_jmeter_data("advertising-service")
crawl_jmeter_data("better-discount-service")
crawl_jmeter_data("discount-tickets-service")
crawl_jmeter_data("meta-service")
crawl_jmeter_data("notice-service")
crawl_jmeter_data("profile-service")
crawl_jmeter_data("message-service")


# In[ ]:




