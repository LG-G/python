#!/usr/bin/env python
# coding: utf-8

# In[3]:


import sys
import urllib.request
import urllib3
import logging
import os


# In[34]:


## run in new-world-gate-010
## cp backup file to jenkins last successfull build

arguments=sys.argv
if len(arguments) <= 2:
    print("usage: {} env service_name. For example, {} test asset-service".format(arguments[0], arguments[0]))
    sys.exit(-1)

ENV=arguments[1]
service=arguments[2]

#ENV="prod"
#ENV="test"
#service="account-service"

if ENV == "prod": 
    ## prod env
    EUREKA_HOST="10.10.0.201:8300"
    MARATHON_HOST="10.10.0.208:3333"
else:
    ## test env
    EUREKA_HOST="10.10.0.215:8300"
    MARATHON_HOST="10.10.0.206:8080"

BACKUP_DIRECTORY="/ws/data/deployment/backup"
JENKINS_JOB_DIRECTORY="/ws/data/jenkins/jobs"
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


# In[39]:


def deploy(service):
    logging.info("Start to deploy service: " + service)
    serviceBuild = "new-world-services" ## test build job
    if ENV == "test":
        if service == "uaa-service":
            service = "new-world-cloud-uaa"
            serviceBuild = "new-world-cloud-build"
    elif ENV == "prod":
        serviceBuild = "new-world-services-prod-build" ## prod build job
        if service == "uaa-service":
            service = "new-world-cloud-uaa"
            serviceBuild = "new-world-cloud-prod-build"
    latestBackupFile = os.popen("ls -tral {}/{}* | tail -1".format(BACKUP_DIRECTORY, service)).read().rstrip()
    if len(latestBackupFile) > 0:
        array = latestBackupFile.split(" ")
        latestBackupFile = array[len(array) - 1]
        a = latestBackupFile.split("/")
        fileName = a[len(a) - 1].split(".jar.")[0] + ".jar"
        destinationFile = "{}/{}/lastSuccessful/archive/{}/build/libs/{}".format(JENKINS_JOB_DIRECTORY, serviceBuild, service, fileName)
        logging.info("cp backup file: {} to jenkins job latest successfull file: {}".format(latestBackupFile, destinationFile))
        os.popen("cp {} {}".format(latestBackupFile, destinationFile)).read()
    logging.info("====End====")


# In[40]:


deploy(service)


# In[ ]:




