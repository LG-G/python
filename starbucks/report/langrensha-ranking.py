#!/usr/bin/env python
# coding: utf-8

# # 安装Mysql 驱动 
# 
# ```python
# pip install sqlalchemy
# ```

# In[3]:


#导入dateframe计算工具
import pandas as pd

#系统及命令行
import sys

from datetime import datetime, date, timedelta
import json
import requests

#发邮件
from starbucks import mail, image, compression

# #行内xi
# %matplotlib inline


# In[4]:


url_prefix = 'http://gateway.fnvalley.com/promotion-service'
# url_prefix = 'http://testgate.fnvalley.com/promotion-service'

# 接口地址
ranking_url = '{}/1.0.0/offline_activity/find_votes_ranking_all/25'.format(url_prefix)
# 收件人邮箱
recipient = 'aki.xie@zan-qian.com'
# 图片存储地址
img_path = '/tmp/langrensha_ranking_image'
# excel地址
excel_path = '/tmp/langrensha.xlsx'
# 附件地址
file_paths = [excel_path, '{}.zip'.format(img_path)]
# 附件显示名称
file_names = ['狼人杀排行榜.xlsx', '狼人杀排行榜头像.zip']


# In[15]:


# 查询狼人杀排行榜数据
ranking_data = requests.get(url=ranking_url)

ranking_json = {}
if ranking_data.status_code == 200:
    ranking_json = json.loads(ranking_data.content.decode('utf8'))

# 排行数据
data_df = ''
if 'data' in ranking_json:
    if len(ranking_json.get('data')) > 0:
        data_df = pd.io.json.json_normalize(ranking_json.get('data'))


data_df.drop(columns=['activityId','joinDate','userActivityId'],axis=1,inplace=True)
data_df.columns = ['手机号', '排名', '入学年份', '头像', '专业', '真实姓名', '学校', '得票数']

data_df.set_index('手机号', inplace=True)

school_df = data_df['学校'].value_counts()
school_df.name = '参加人数'


# In[10]:


# 生成 excel
writer = pd.ExcelWriter(excel_path)

data_df.to_excel(writer, sheet_name='排行榜')
writer.save()

school_df.to_excel(writer, sheet_name='学校报名情况', index_label='学校名称')
writer.save()


# In[21]:


for item in data_df['头像'].items():
    if item[1] is not None:
        image.download_image(url=item[1], file_path='{}/{}.jpg'.format(img_path, item[0]))

# 压缩文件夹
compression.make_zip(img_path, '{}.zip'.format(img_path))


# In[20]:


# 发送带附件的邮件
mail.send_mail_attachments(file_path=file_paths, file_name=file_names, recipient=recipient, subject="狼人杀排行榜")


# In[ ]:




