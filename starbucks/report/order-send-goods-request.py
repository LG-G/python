#!/usr/bin/env python
# coding: utf-8

# # 安装Mysql 驱动 
# 
# ```python
# pip install sqlalchemy
# ```

# In[1]:


#导入dateframe计算工具
import pandas as pd

#mysql 数据源工具
import sqlalchemy as db

#系统及命令行
import sys

from datetime import datetime
import json
import requests
import logging

logging.getLogger().setLevel(logging.INFO)


# In[61]:


logging.info('------------ datetime_now : {}------------'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
logging.info('==========================  发货 API start  ==========================')

# ACCESS_TOKEN="4f55964d-d361-44fe-94d8-2f2eaedce16e"
ACCESS_TOKEN="0388e2d7-61f1-4588-ab8c-16e9d5dd98e3"

# sys.argv = ["", "local", "/Users/jiangmin/Downloads/金猪活动兑换明细.xlsx"]

# 环境
env = sys.argv[1]
# 文件地址
file_path = sys.argv[2]

if str(env) == 'test':
    send_goods_url="http://testgate.zan-qian.com/order-service/1.0.0/order/order_send_goods"
elif str(env) == 'prod':
    send_goods_url="http://gateway.zan-qian.com/order-service/1.0.0/order/order_send_goods"
elif str(env) == 'local':
    send_goods_url="http://127.0.0.1:9010/1.0.0/order/order_send_goods"
else:
    send_goods_url="http://testgate.zan-qian.com/order-service/1.0.0/order/order_send_goods"

# log 参数信息
logging.info('-----  env={}, file_path={}  -----'.format(env, file_path))
logging.info('-----  send_goods_url={}  -----'.format(send_goods_url))


# In[ ]:


excel_df = pd.read_excel(file_path, index_col='订单号')
headers = {'Authorization': 'Bearer {}'.format(ACCESS_TOKEN), 'Content-Type': 'application/json'}

for index,data in excel_df.iterrows():
    if (data['订单状态'] == '等待发货'):
        request_param = {'orderNo':index}
        response = requests.post(url=send_goods_url, data=json.dumps(request_param), headers=headers)
        logging.info('-----  requests orderNo={}, code={}, content={}  -----'.format(index, response.status_code, response.content))


# In[ ]:


logging.info('==========================  发货 API end  ==========================')


# In[ ]:




