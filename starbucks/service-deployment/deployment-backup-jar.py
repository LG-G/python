#!/usr/bin/env python
# coding: utf-8

# In[137]:


import sys
import urllib.request
import urllib3
import xml.etree.ElementTree as ET
from datetime import datetime
import time
import json
import logging
import os


# In[117]:


arguments=sys.argv
if len(arguments) <= 2:
    print("usage: {} env service_name. For example, {} test asset-service".format(arguments[0], arguments[0]))
    sys.exit(-1)

ENV=arguments[1]
service=arguments[2]

#ENV="prod"
#ENV="test"
#service="uaa-service"

if ENV == "prod": 
    ## prod env
    EUREKA_HOST="10.10.0.201:8300"
    MARATHON_HOST="10.10.0.208:3333"
else:
    ## test env
    EUREKA_HOST="10.10.0.215:8300"
    MARATHON_HOST="10.10.0.206:8080"

ACCESS_TOKEN="4f55964d-d361-44fe-94d8-2f2eaedce16e"
TIMEOUT=10
BACKUP_DIRECTORY="/ws/data/deployment/backup"
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


# In[130]:


def queryInstances(service):
    serviceType = "service"
    if service.startswith("uaa"):
        serviceType = "cloud"
    marathon_current_instance_url = "http://{}/v2/apps/{}/{}/{}?embed=app.taskStats&embed=app.readiness".format(MARATHON_HOST, ENV, serviceType, service)
    print(marathon_current_instance_url)
    response = urllib.request.urlopen(marathon_current_instance_url, timeout=TIMEOUT).read()
    responseJson = json.loads(response.decode('utf8'))
    hostData = {}
    for task in responseJson["app"]["tasks"]: 
        if len(task["ports"]) > 0:
            hostData[task["id"]] = task["ipAddresses"][0]["ipAddress"] + ":" + str(task["ports"][0])
        else:
            env = responseJson["app"]["env"]
            if env.get("PORT0") != None:
                hostData[task["id"]] = task["ipAddresses"][0]["ipAddress"] + ":" + str(env.get("PORT0"))
    return hostData


# In[131]:


def deploy(service):
    logging.info("Start to deploy service: " + service)
    marathonService = service
    eurekaService = service
    if ENV == "test":
        if service == "uaa-service":
            marathonService = "uaa-dev-db-prod-redis"
            eurekaService = "new-world-cloud-uaa"
        elif service == "profile-service":
            marathonService = "profile-service-test-db"
        elif service == "account-service":
            marathonService = "account-service-test-db"
    elif ENV == "prod":
        if service == "uaa-service":
            eurekaService = "new-world-cloud-uaa"
            marathonService = "uaa"
    oldHostData = queryInstances(marathonService)
    logging.info("Current instances: " + str(oldHostData))
    if len(oldHostData) == 0:
        logging.warnning("Not instance found. Stop the script!!!")
        sys.exit(-1)
    
    for instanceId in oldHostData.keys():
        hostPort = oldHostData[instanceId]
        host = hostPort.split(":")[0]
        port = hostPort.split(":")[1]
        logging.info("Get the jar file of current instance: " + hostPort)
        command = "ps -ef | grep " + eurekaService + " | grep " + host + " | grep " + port + " | sed 's/nw\s\+\([0-9]\+\)\s\+.*/\\1/g' | xargs -i ls -l /proc/{}/fd | grep '" + eurekaService + ".*.jar' | sed 's%.*\s\+\(/ws/data/.*.jar\)%\\1%g' | uniq"
        file = os.popen("ssh -q -o 'StrictHostKeyChecking no' {} \"{}\"".format(host, command)).read().rstrip()
        if len(file) > 0:
            pathArray = file.split("/")
            fileName = pathArray[len(pathArray) - 1]
            backupFile = "{}/{}.{}".format(BACKUP_DIRECTORY, fileName, datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
            logging.info("Scp file {}:{} to {}".format(host, file, backupFile))
            os.popen("scp -q -o 'StrictHostKeyChecking no' nw@{}:{} {}".format(host, file, backupFile)).read()
        break
    
    logging.info("====End====")


# In[132]:


deploy(service)


# In[ ]:




