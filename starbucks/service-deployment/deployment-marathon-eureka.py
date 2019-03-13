#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import sys
import urllib.request
import urllib3
import xml.etree.ElementTree as ET
import datetime
import time
import json
import logging


# In[111]:


logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

arguments=sys.argv
if len(arguments) <= 4:
    logging.info("usage: {} env service_name new_scala_number remove_old_instance_or_not. For example, {} test asset-service 1 True".format(arguments[0], arguments[0]))
    sys.exit(-1)

newScalaNumber=0
try:
    newScalaNumber = int(arguments[3])
except:
    logging.info("usage: {} env service_name new_scala_number remove_old_instance_or_not. For example, {} test asset-service 1 True".format(arguments[0], arguments[0]))
    sys.exit(-1)
autoRemove = False
if len(arguments) >= 5 && arguments[4] == "True" or arguments[4] == "true":
    autoRemove = True

service=arguments[2]
ENV=arguments[1]
##ENV="prod"
##ENV="test"
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


# In[79]:


def queryInstances(service):
    serviceType = "service"
    if service.startswith("uaa"):
        serviceType = "cloud"
    marathon_current_instance_url = "http://{}/v2/apps/{}/{}/{}?embed=app.taskStats&embed=app.readiness".format(MARATHON_HOST, ENV, serviceType, service)
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


# In[ ]:


def deployFixPortService(service, marathonFolder, marathonService):
    oldHostData = queryInstances(marathonService)
    logging.info("Current instances: " + str(oldHostData))
    marathon_new_instance_url = "http://{}/v2/apps/{}/{}/{}".format(MARATHON_HOST, ENV, marathonFolder, marathonService)
    data = '{"instances":0}'
    http = urllib3.PoolManager()
    ## suspend current instance
    response = http.request("PUT", marathon_new_instance_url, body=data.encode("utf-8"))
    time.sleep(10)
    data = '{"instances":1}'
    response = http.request("PUT", marathon_new_instance_url, body=data.encode("utf-8"))
    time.sleep(10)
    newHostData = queryInstances(marathonService)
    count = 0
    ## check the new instance has been started by marathon
    while len(newHostData) < scale_number and count < 10:
        time.sleep(10)
        newHostData = queryInstances(marathonService)
        count = count + 1
    if len(newHostData) < scale_number:
        logging.error("Deployment is not successfull. May be mesos resource is not enough!")
        sys.exit(-1)
    logging.info("New and old instances: " + str(newHostData))


# In[122]:


def deploy(service, newScala = 1, autoRemove = False):
    logging.info("Start to deploy service: " + service)
    marathonService = service
    eurekaService = service
    marathonFolder = "service"
    if ENV == "test":
        if service == "uaa-service":
            marathonService = "uaa-dev-db-prod-redis"
            eurekaService = "new-world-cloud-uaa"
            marathonFolder = "cloud"
        elif service == "profile-service":
            marathonService = "profile-service-test-db"
        elif service == "account-service":
            marathonService = "account-service-test-db"
    elif ENV == "prod":
        if service == "uaa-service":
            eurekaService = "new-world-cloud-uaa"
            marathonService = "uaa"
            marathonFolder = "cloud"
    if service == "notification-service":
        deployFixPortService(service, marathonFolder, marathonService)
        return ""
    oldHostData = queryInstances(marathonService)
    logging.info("Current instances: " + str(oldHostData))
    
    marathon_new_instance_url = "http://{}/v2/apps/{}/{}/{}".format(MARATHON_HOST, ENV, marathonFolder, marathonService)
    scale_number = len(oldHostData) + newScala
    data = '{"instances":' + str(scale_number) + '}'
    http = urllib3.PoolManager()
    ## start one more instance in marathon
    response = http.request("PUT", marathon_new_instance_url, body=data.encode("utf-8"))
    time.sleep(10)
    newHostData = queryInstances(marathonService)
    count = 0
    ## check the new instance has been started by marathon
    while len(newHostData) < scale_number and count < 10:
        time.sleep(10)
        newHostData = queryInstances(marathonService)
        count = count + 1
    if len(newHostData) < scale_number:
        logging.error("Deployment is not successfull. May be mesos resource is not enough!")
        sys.exit(-1)
    logging.info("New and old instances: " + str(newHostData))
    
    time.sleep(20)
    ## healthcheck of new instance by actuator health link
    for instanceId in newHostData.keys():
        if oldHostData.get(instanceId) == None:
            hostPort = newHostData[instanceId]
            healthCheckUrl = "http://{}/actuator/health".format(hostPort)
            healthCheckCount = 0
            while healthCheckCount < 10:
                try:
                    response = http.request("get", healthCheckUrl)
                    if response.status == 200:
                        healthCheckCount = 100 # break the while loop
                        logging.info("Health check is UP")
                    else:
                        time.sleep(10)
                        logging.warning("Health check count: {}, with status: {}".format(healthCheckCount, response.status))
                except:
                    time.sleep(10)
                    logging.warning("Health check count: {}, with error by http request".format(healthCheckCount))
                healthCheckCount = healthCheckCount + 1
            if healthCheckCount == 10:
                logging.error("Instance is not up after 10 retries of health check")
                sys.exit(-1)
    
    time.sleep(5)
    logging.info("Put service to out of service")
    ## set old instance to OUT_OF_SERVICE
    for instanceId in oldHostData.keys():
        hostPort = oldHostData[instanceId]
        outOfServiceUrl = "http://{}/eureka/apps/{}/{}/status?value=OUT_OF_SERVICE".format(EUREKA_HOST, eurekaService, hostPort)
        response = http.request("PUT", outOfServiceUrl)
        
    if autoRemove == True:
        if ENV == "test":
            logging.info("Sleep 1.5 minutes before remove old instances")
            time.sleep(90)
        else:
            logging.info("Sleep 5 minutes before remove old instances")
            time.sleep(300)
        ids = []
        for instanceId in oldHostData.keys():
            ids.append(instanceId)
        logging.info("Ids are to be removed: " + str(ids))
        removeInstanceUrl = "http://{}/v2/tasks/delete?scale=true".format(MARATHON_HOST)
        data = {"ids": ids}
        response = http.request("POST", removeInstanceUrl, body=json.dumps(data).encode("utf-8"))  
    logging.info("====End====")


# In[123]:


deploy(service, newScalaNumber, autoRemove)

