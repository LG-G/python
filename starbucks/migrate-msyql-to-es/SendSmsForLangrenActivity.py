#!/usr/bin/env python
# coding: utf-8

# In[36]:


#导入dateframe计算工具
import pandas as pd

# #导入绘图工具
# import matplotlib.pyplot as plt
# #一般作为机器学习绘图用, 但是也能绘出更cool的图
# import seaborn as sns

#mysql 数据源工具
import sqlalchemy as db

#系统及命令行
import sys

import json

import urllib.request
import ssl
from urllib.parse import quote
import string


# In[37]:


arguments=sys.argv
if len(arguments) <= 4:
    print("usage: {} db_host db_user db_password esHost. For example, {} 10.10.0.215:3306 root 82f12dbf497b".format(arguments[0], arguments[0]))
    #sys.exit(-1)

profile_db = "10.10.0.198:3306"
username = "root"
password = "root"

sms_host = 'https://feginesms.market.alicloudapi.com'
sms_path = '/codeNotice'
sms_appcode = 'b37f2cb3d2d34c05a51798fa0872ea0b'
sms_sign = '43252'
sms_skin = '33642'

#profile_db = sys.argv[1]
#username = sys.argv[2]
#password = sys.argv[3]

print("database: {}, username: {}, password: {}".format(profile_db, username, password))

mysql_conn_str = 'mysql+pymysql://{}:{}@{}/order_service?charset=utf8mb4'.format(username, password, profile_db)

user_profile_query = '''select DISTINCT phone_number as phone from order_service.order_v1 where phone_number in 
                           (select login_id from account_service.sys_account)'''


# In[38]:


try:
    engine = db.create_engine(mysql_conn_str)
    connection = engine.connect()
    df = pd.read_sql_query(user_profile_query, connection)
except:
    print("读取数据错误")
    raise "读取数据错误"
connection.close()


# In[39]:


def sendSmsMessage(phone):
    print("Send sms to: " + phone)
    url = '{}{}?param=&phone={}&sign={}&skin={}'.format(sms_host, sms_path, phone, sms_sign, sms_skin)
    bodys = {}
    newurl = quote(url,safe=string.printable)
    request = urllib.request.Request(newurl)
    request.add_header('Authorization', 'APPCODE ' + sms_appcode)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    response = urllib.request.urlopen(request, context=ctx)
    content = response.read()
    if (content):
        print(content.decode('UTF-8'))


# In[40]:


print("data size: " + df.size)
for row in df.values:
    phone = row[0]
    print("Phone: " + phone)
    #sendSmsMessage(phone)
sendSmsMessage("13788921587")


# In[ ]:




