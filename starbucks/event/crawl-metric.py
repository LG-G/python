#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import urllib.request
import xml.etree.ElementTree as ET
import datetime
import time
import json


# In[2]:


EUREKA_HOST="10.10.0.201:8300"
INFLUXDB_HOST="10.10.0.214:8086"
#EUREKA_HOST="10.10.0.215:8300"
#INFLUXDB_HOST="10.10.0.208:8086"
INFLUXDB_DATABASE="cityzone"
ACCESS_TOKEN="4f55964d-d361-44fe-94d8-2f2eaedce16e"
DATE_TIME=int(time.time()) * 1000000000
HTTP_REQUEST_METRIC_NAME="http.server.requests"
TIMEOUT=10
postUrl = "http://{}/write?db={}".format(INFLUXDB_HOST, INFLUXDB_DATABASE)


# In[3]:


def sendServiceStatus(service, hostPort, status):
    statusCode = 0
    if status == "UP":
        statusCode = 5
    data = "servicestatus,service={},host={} status={} {}".format(service, hostPort, statusCode, DATE_TIME)
    urllib.request.urlopen(url = postUrl, data = data.encode('utf-8'))


# In[4]:


def sendMeasurement(service, hostPort, measurementName, measurement):
    tags = measurement["tags"]
    data = measurement["data"]
    tagNames = "service={},host={}".format(service, hostPort)
    for tag in tags:
        tagNames += "," + tag["key"] + "=" + tag["value"].replace(" ", "\\ ")
    for metricData in data:
        if metricData["statistic"] != "MAX":
            postData = "{},{} {}={} {}".format(measurementName, tagNames, metricData["statistic"], metricData["value"], DATE_TIME)
            urllib.request.urlopen(url = postUrl, data = postData.encode('utf-8'))


# In[5]:


def aggregateHttpError(measurement):
    tags = measurement["tags"]
    data = measurement["data"]
    for tag in tags:
        if tag["key"] == "status" and (int(int(tag["value"]) / 100) == 4 or int(int(tag["value"]) / 100) == 5):
            for metricData in data:
                if metricData["statistic"] == "COUNT":
                    return metricData["value"]
    return 0


# In[6]:


def sendHttpRequestMetric(service, hostPort, requestMetric):
    measurementName="requests"
    metricNameCount = "COUNT"
    metricValueCount = 0
    metricNameAvgTime = "AVG_TIME"
    metricValueAvgTime = 0
    metricNameTotalTime = "TOTAL_TIME"
    metricValueTotalTime = 0
    metricNameError = "ERROR"
    metricValueError = 0 
    for m in requestMetric["summary"]:
        statistic = m["statistic"]
        value = m["value"]
        if statistic == "COUNT":
            metricValueCount = value
        elif statistic == "TOTAL_TIME":
            metricValueTotalTime = value
    
    if metricValueCount > 0:
        metricValueAvgTime = metricValueTotalTime / metricValueCount
        
    for measurement in requestMetric["measurements"]:
        sendMeasurement(service, hostPort, measurementName, measurement)
        metricValueError += aggregateHttpError(measurement)
    
    postData = "{},service={},host={},uri=total,status=total,method=ALL {}={},{}={},{}={},{}={} {}".format(measurementName,service,hostPort,metricNameCount,metricValueCount,metricNameTotalTime,metricValueTotalTime,metricNameAvgTime,metricValueAvgTime,metricNameError,metricValueError,DATE_TIME)
    urllib.request.urlopen(url = postUrl, data = postData.encode('utf-8'))


# In[7]:


def sendJvmMemoryUsed(service, hostPort, metricData):
    for measurement in metricData["measurements"]:
        sendMeasurement(service, hostPort, "jvmmemory", measurement)


# In[8]:


def sendGcPause(service, hostPort, metricData):
    for measurement in metricData["measurements"]:
        sendMeasurement(service, hostPort, "gcpause", measurement)


# In[9]:


def sendHikaricpConnection(service, hostPort, dataType, metricData):
    measurementName="hikaricp.connections"
    tagData = []
    for m in metricData["summary"]:
        statistic = m["statistic"]
        value = m["value"]
        if statistic != "MAX":
            tagData.append("{}={}".format(statistic,value))
    if len(tagData) > 0:
        postData = "{},service={},host={},type={} {} {}".format(measurementName,service,hostPort,dataType,",".join(tagData),DATE_TIME)
        urllib.request.urlopen(url = postUrl, data = postData.encode('utf-8'))


# In[10]:


def sendHibernateMetric(service, hostPort, dataType, metricData):
    measurementName="hibernate"
    if len(metricData["summary"]) == 1:
        m = metricData["summary"][0]
        value = m["value"]
        postData = "{},service={},host={} {}={} {}".format(measurementName,service,hostPort,dataType,value,DATE_TIME)
        urllib.request.urlopen(url = postUrl, data = postData.encode('utf-8'))
    if dataType == "transactions":
        for measurement in metricData["measurements"]:
            tags = measurement["tags"]
            if len(tags) == 1 and tags[0]["key"] == "result" and tags[0]["value"] == "failure":
                value = measurement["data"][0]["value"];
                postData = "{},service={},host={} {}={} {}".format(measurementName,service,hostPort,"failure",value,DATE_TIME)
                urllib.request.urlopen(url = postUrl, data = postData.encode('utf-8'))


# In[11]:


def sendDeferredMetric(service, hostPort, dataType, metricData):
    measurementName="deferredresult"
    if len(metricData["summary"]) == 1:
        m = metricData["summary"][0]
        value = m["value"]
        postData = "{},service={},host={} {}={} {}".format(measurementName,service,hostPort,dataType,value,DATE_TIME)
        urllib.request.urlopen(url = postUrl, data = postData.encode('utf-8'))


# In[12]:


## send actuator metric including http request, jvm memory, jvm gc
def sendActuatorMetric(service, hostPort):
    try: 
        includingMetric="http.server.requests:uri;method;status,jvm.memory.used:area,jvm.gc.pause:cause,hikaricp.connections.usage,hikaricp.connections.pending,hikaricp.connections.active"
        includingMetric+=",hibernate.statements:status,hibernate.query.executions,hibernate.query.executions.max,hibernate.transactions:result"
        includingMetric+=",deferredresult.connecting,deferredresult.complete,deferredresult.timeout"
        url = "http://{}/actuator/custom-metrics?includingMetric={}&access_token={}".format(hostPort, includingMetric, ACCESS_TOKEN)
        response = urllib.request.urlopen(url,timeout=TIMEOUT).read()
        responseJson = json.loads(response.decode('utf8'))
        for metricData in responseJson:
            name = metricData["name"]
            if name == "http.server.requests":
                sendHttpRequestMetric(service, hostPort, metricData)
            elif name == "jvm.memory.used":
                sendJvmMemoryUsed(service, hostPort, metricData)
            elif name == "jvm.gc.pause":
                sendGcPause(service, hostPort, metricData)
            elif name.startswith("hikaricp.connections."):
                dataType = name[len("hikaricp.connections."):]
                sendHikaricpConnection(service, hostPort, dataType, metricData)
            elif name.startswith("hibernate."):
                dataType = name[len("hibernate."):]
                sendHibernateMetric(service, hostPort, dataType, metricData)
            elif name.startswith("deferredresult."):
                dataType = name[len("deferredresult."):]
                sendDeferredMetric(service, hostPort, dataType, metricData)
                
    except urllib.error.HTTPError as httpError:
        print("Error when get actuator metrics with status code: " + str(httpError.code))


# In[13]:


def crawl_metric(service):
    try:
        print("Service is " + service)
        response = urllib.request.urlopen("http://" + EUREKA_HOST + "/eureka/apps/" + service, timeout=TIMEOUT)
        html = response.read()
        root = ET.fromstring(html)
        if service == "new-world-cloud-uaa":
            service = "uaa-service"
        for instance in root.findall("instance"):
            ip = instance.find("ipAddr").text
            port = instance.find("port").text
            status = instance.find("status").text
            hostPort = ip + ":" + port
            print(hostPort + " => " + status)
            sendServiceStatus(service, hostPort, status)
            sendActuatorMetric(service, hostPort)
    except:
        print("Exception to get metric of service: " + service)


# In[14]:


crawl_metric("advertising-service")
crawl_metric("better-discount-service")
crawl_metric("asset-service")
crawl_metric("new-world-cloud-uaa")
crawl_metric("task-service")
crawl_metric("game-service")
crawl_metric("profile-service")
crawl_metric("promotion-service")
crawl_metric("account-service")
crawl_metric("meta-service")
crawl_metric("discount-tickets-service")
crawl_metric("signin-service")
crawl_metric("notice-service")
crawl_metric("message-service")
crawl_metric("payment-service")
crawl_metric("order-service")
crawl_metric("besttv-service")
crawl_metric("contact-service")
crawl_metric("game-service")
crawl_metric("building-show-service")
crawl_metric("3rd-content-service")
crawl_metric("item-service")
crawl_metric("notification1-service")

