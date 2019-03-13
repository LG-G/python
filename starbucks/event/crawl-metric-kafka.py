#!/usr/bin/env python
# coding: utf-8

# In[71]:


import sys
import urllib.request
import urllib3
import logging
import os


# In[72]:


KAFKA_HOST="new-world-gate-008"
KAFKA_BROKER="10.10.0.214:9092"
PROMETHEUS_PUSHGATEWAY="10.10.0.214:9091"
postUrl = "http://{}/metrics/job/kafkaMetric".format(PROMETHEUS_PUSHGATEWAY)
groupTopicPair = [["message-notification-prod1", "message_v2-prod1"], 
                  ["message-notification-test", "message_v2-test"],
                  ["kafkaListener", "event-prod"],
                  ["kafkaListener", "event-test"],
                  ["smart-scan-event-prod", "event_v2-prod"],
                  ["smart-scan-event-test", "event_v2-test"],
                  ["event-flink", "event_v2-prod"],
                  ["event-flink", "event_v2-test"]
]
#command = "export JAVA_HOME=/ws/program/jdk;/ws/program/kafka/bin/kafka-consumer-groups.sh --bootstrap-server 10.10.0.214:9092 --describe --group message-notification-prod1 | grep message_v2-prod1"
#data=os.popen("ssh -q -o 'StrictHostKeyChecking no' nw@{} \"{}\"".format(kafkaHost, command)).read().rstrip()


# In[73]:


def getTopicInfo(group, topic, result):
    command = "export JAVA_HOME=/ws/program/jdk;/ws/program/kafka/bin/kafka-consumer-groups.sh --bootstrap-server {} --describe --group {} | grep {}".format(KAFKA_BROKER, group, topic)
    data = os.popen("ssh -q -o 'StrictHostKeyChecking no' nw@{} \"{}\"".format(KAFKA_HOST, command)).read().rstrip()
    for line in data.split("\n"): 
        topicPartitionInfo = line.split()
        partition = topicPartitionInfo[1]
        endOffset = topicPartitionInfo[3]
        lag = topicPartitionInfo[4]
        result.append([group, topic, partition, endOffset, lag])


# In[74]:


result = []
for groupTopic in groupTopicPair:
    getTopicInfo(groupTopic[0], groupTopic[1], result)


# In[75]:


if len(result) > 0:
    postData = ""
    for topicPartitionInfo in result:
        postData += """kafkaEndOffsetMetric{{group="{}",topic="{}",partition="{}"}} {}\n""".format(topicPartitionInfo[0], topicPartitionInfo[1], topicPartitionInfo[2], topicPartitionInfo[3])
        postData += """kafkaLagMetric{{group="{}",topic="{}",partition="{}"}} {}\n""".format(topicPartitionInfo[0], topicPartitionInfo[1], topicPartitionInfo[2], topicPartitionInfo[4])
    urllib.request.urlopen(url = postUrl, data = postData.encode('utf-8'))


# In[ ]:




