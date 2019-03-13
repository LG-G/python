#!/usr/bin/env python
# coding: utf-8

# # 安装Mysql 驱动 
# 
# ```python
# pip install sqlalchemy
# ```

# In[56]:


#导入dateframe计算工具
import pandas as pd

# #导入绘图工具
# import matplotlib.pyplot as plt
# #一般作为机器学习绘图用, 但是也能绘出更cool的图
# import seaborn as sns

#行内xi
# %matplotlib inline

#mysql 数据源工具
import sqlalchemy as db

#系统及命令行
import sys

from datetime import datetime
import json
import logging

logging.getLogger().setLevel(logging.INFO)

#发邮件
from starbucks import mail


# In[ ]:


logging.info('------------ datetime_now : {}------------'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
logging.info('==========================  销帐报表 start  ==========================')

# sys.argv = ["", "test", "月", "jiangmin@zan-qian.com", "2019-02-01", "2019-02-28"]

# 环境
env = sys.argv[1]
# 报表描述
report_desc = sys.argv[2]
# 邮件收件人
recipient = sys.argv[3]
# 开始时间
start_date = sys.argv[4]
# 结束时间
end_date = str(sys.argv[4])

if len(sys.argv) > 5:
    end_date = sys.argv[5]

if str(env) == 'test':
    db_01 = 'root:82f12dbf497b@10.10.0.215'
    db_02 = 'root:82f12dbf497b@10.10.0.215'
elif str(env) == 'prod':
    db_01 = 'cityzone:Hellowrold@123@cityzone-service.mysql.rds.aliyuncs.com:3306'
    db_02 = 'cityzone:Hellowrold@123@cityzone-resources.mysql.rds.aliyuncs.com:3306'
else:
    db_01 = 'root:82f12dbf497b@10.10.0.215'
    db_02 = 'root:82f12dbf497b@10.10.0.215'

# log 参数信息
logging.info('-----  env={}, start_date={}, end_date={}  -----'.format(env, start_date, end_date))
logging.info('-----  db_01={}  -----'.format(db_01))
logging.info('-----  db_02={}  -----'.format(db_02))
logging.info('-----  recipient={}  -----'.format(recipient))


# In[58]:


mysql_elimination_conn_str = 'mysql+pymysql://{}/elimination_service?charset=utf8mb4'.format(db_02)

# 清帐状态增加一个 “无需清帐”金额小于0.1， 小于0.1的金额，认为是已清帐
# 积分卡券使用总结sql 
use_asset_summary_query = '''select t1.date as '日期', t1.consumption_number '用户消费次数(次)', t1.consumption_amount '用户消费总金额(元)', t1.top_up_amount '积分充值智能校园(元)', t1.deduction_amount '卡券抵扣智能校园(元)', t1.elimination_amount '需要清账金额(元)',
                    (select sum(amount) from elimination_trace t2 where t1.date=t2.date and (t2.`status`='success' or t2.`status`='no_need')) as '已经清账金额(元)',
                    if ((select sum(amount) from elimination_trace t2 where t1.date=t2.date and (t2.`status`='success' or t2.`status`='no_need'))>=t1.elimination_amount, '是','否') as '是否完结'
                    FROM `use_asset_trace` t1 
                    WHERE t1.`date` >= '{0}' and DATE_FORMAT(t1.`date`,'%%Y-%%m-%%d') <= '{1}' '''

# 打款情况总结sql
elimination_summary_query = '''select date as '日期', merchant_name '商户', amount '金额'
                    from `elimination_trace`
                    where `date` >= '{0}' and DATE_FORMAT(`date`,'%%Y-%%m-%%d') <= '{1}' 
                    and (`status`='success' or `status`='no_need') '''

# 积分卡券使用总结
def get_use_asset_summary(start_date, end_date):
    try:
        engine = db.create_engine(mysql_elimination_conn_str)
        connection = engine.connect()
        
        df = pd.read_sql_query(use_asset_summary_query.format(start_date, end_date), connection)
    except:
        print("读取数据错误")
        raise "读取数据错误"
    connection.close()
    return df

# 打款情况总结
def get_elimination_summary(start_date, end_date):
    try:
        engine = db.create_engine(mysql_elimination_conn_str)
        connection = engine.connect()
        
        df = pd.read_sql_query(elimination_summary_query.format(start_date, end_date), connection)
    except:
        print("读取数据错误")
        raise "读取数据错误"
    connection.close()
    return df


# In[64]:


# 积分卡券使用总结
use_asset_df = get_use_asset_summary(start_date, end_date)
# 打款情况总结
elimination_df = get_elimination_summary(start_date, end_date)


# In[65]:


# ----------------------------积分卡券使用总结----------------------------
# def reset_end(df):
#     if df['需要清账金额(元)'] == 0:
#         df['是否完结'] = '是'
#     return df
# def reset_date_str(df):
#     df['日期'] = df['日期'].strftime("%Y-%m-%d")
#     return df

# NaN数据改为0
use_asset_df.fillna(value=0, inplace=True)

# 不需要清账的数据，改为已完结
# use_asset_df = use_asset_df.apply(reset_end, axis=1)
use_asset_df.loc[use_asset_df[use_asset_df['需要清账金额(元)'] == 0].index, '是否完结'] = '是'

# 日期格式改为字符串
# use_asset_df = use_asset_df.apply(reset_date_str, axis=1)
use_asset_df[['日期']] = use_asset_df[['日期']].astype(str)

use_asset_df.set_index('日期', inplace=True)

# 积分卡券使用总结 数据反转
# use_asset_df = use_asset_df.T


# In[70]:


# ----------------------------商户打款总结----------------------------
# 日期格式改为字符串
elimination_df[['日期']] = elimination_df[['日期']].astype(str)

if len(elimination_df) > 0:
    elimination_df = elimination_df.groupby(['日期','商户']).sum()['金额'].to_frame()
else:
    elimination_df = pd.DataFrame(columns=['商户', '金额'])


# In[71]:


# # 生成 excel
writer = pd.ExcelWriter('/tmp/{}.xlsx'.format(start_date))

use_asset_df.to_excel(writer, sheet_name='积分卡券使用总结', index_label='日期')
elimination_df.to_excel(writer, sheet_name='打款情况总结', index_label=['日期', '商户'])

writer.save()


# In[ ]:


# 发送带附件的邮件
mail.send_mail_attachment(file_path='/tmp/{}.xlsx'.format(start_date), file_name='统计.xlsx', recipient=recipient, subject=report_desc)


# In[ ]:


logging.info('==========================  销帐报表 end  ==========================')


# In[ ]:




