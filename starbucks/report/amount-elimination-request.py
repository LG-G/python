#!/usr/bin/env python
# coding: utf-8

# # 安装Mysql 驱动 
# 
# ```python
# pip install sqlalchemy
# ```

# In[39]:


#导入dateframe计算工具
import pandas as pd

# #导入绘图工具
# import matplotlib.pyplot as plt
# #一般作为机器学习绘图用, 但是也能绘出更cool的图
# import seaborn as sns

# #行内xi
# %matplotlib inline

#mysql 数据源工具
import sqlalchemy as db

#系统及命令行
import sys

from datetime import datetime
import json
import requests
import logging

logging.getLogger().setLevel(logging.INFO)


# In[ ]:


logging.info('------------ datetime_now : {}------------'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
logging.info('==========================  销帐 API start  ==========================')

ACCESS_TOKEN="4f55964d-d361-44fe-94d8-2f2eaedce16e"

# env = 'test'
# start_date = '2018-11-22'
# end_date = '2018-12-11'

# 环境
env = sys.argv[1]
# 开始时间
start_date = sys.argv[2]
# 结束时间
end_date = str(sys.argv[2])

if len(sys.argv) > 3:
    end_date = sys.argv[3]

if str(env) == 'test':
    eliminate_url="http://testgate.zan-qian.com/payment-service/1.0.0/xian_campus/eliminate"
elif str(env) == 'prod':
    eliminate_url="http://gateway.zan-qian.com/payment-service/1.0.0/xian_campus/eliminate"
elif str(env) == 'local':
    eliminate_url="http://127.0.0.1:9001/1.0.0/xian_campus/eliminate"
else:
    eliminate_url="http://testgate.zan-qian.com/payment-service/1.0.0/xian_campus/eliminate"

# log 参数信息
logging.info('-----  env={}, start_date={}, end_date={}  -----'.format(env, start_date, end_date))
logging.info('-----  eliminate_url={}  -----'.format(eliminate_url))


# In[ ]:


request_param = {'startDate':start_date, 'endDate':end_date}
headers = {'Authorization': 'Bearer {}'.format(ACCESS_TOKEN)}

# 发起销帐请求
response = requests.post(url=eliminate_url, data=request_param, headers=headers)

logging.info('-----  requests code={}  -----'.format(response.status_code))
logging.info('-----  requests content={}  -----'.format(response.content))

logging.info('==========================  销帐 API end  ==========================')


# In[ ]:




