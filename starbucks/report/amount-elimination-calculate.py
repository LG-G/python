#!/usr/bin/env python
# coding: utf-8

# # 安装Mysql 驱动 
# 
# ```python
# pip install sqlalchemy
# ```

# In[58]:


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

from datetime import datetime, timedelta
import json
import requests
import logging

logging.getLogger().setLevel(logging.INFO)


# In[ ]:


logging.info('------------ datetime_now : {}------------'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
logging.info('==========================  销帐计算 start  ==========================')

# env = 'test'
# start_date = datetime.strptime('2018-12-10', "%Y-%m-%d")
# end_date = datetime.strptime('2018-12-12', "%Y-%m-%d")

# 环境
env = sys.argv[1]
# 开始时间
start_date = datetime.strptime(sys.argv[2], "%Y-%m-%d")
# 结束时间
end_date = datetime.strptime(sys.argv[2], "%Y-%m-%d")

if len(sys.argv) > 3:
    end_date = datetime.strptime(sys.argv[3], "%Y-%m-%d")

if str(env) == 'test':
    eliminate_url="http://testgate.zan-qian.com/payment-service/1.0.0/xian_campus/eliminate?startDate={}&endDate={}".format(start_date, end_date)
    db_01 = 'root:82f12dbf497b@10.10.0.215'
    db_02 = 'root:82f12dbf497b@10.10.0.215'
elif str(env) == 'prod':
    eliminate_url="http://gateway.zan-qian.com/payment-service/1.0.0/xian_campus/eliminate?startDate={}&endDate={}".format(start_date, end_date)
    db_01 = 'cityzone:Hellowrold@123@cityzone-service.mysql.rds.aliyuncs.com:3306'
    db_02 = 'cityzone:Hellowrold@123@cityzone-resources.mysql.rds.aliyuncs.com:3306'
else:
    eliminate_url="http://127.0.0.1:9001/1.0.0/xian_campus/eliminate?startDate={}&endDate={}".format(start_date, end_date)
    db_01 = 'root:82f12dbf497b@10.10.0.215'
    db_02 = 'root:82f12dbf497b@10.10.0.215'

# log 参数信息
logging.info('-----  env={}, start_date={}, end_date={}  -----'.format(env, start_date, end_date))
logging.info('-----  eliminate_url={}  -----'.format(eliminate_url))
logging.info('-----  db_01={}  -----'.format(db_01))
logging.info('-----  db_02={}  -----'.format(db_02))


# In[66]:


mysql_asset_conn_str = 'mysql+pymysql://{}/asset_service?charset=utf8mb4'.format(db_01)
mysql_discount_conn_str = 'mysql+pymysql://{}/discount_tickets_service?charset=utf8mb4'.format(db_02)
mysql_order_conn_str = 'mysql+pymysql://{}/order_service?charset=utf8mb4'.format(db_02)
mysql_elimination_conn_str = 'mysql+pymysql://{}/elimination_service?charset=utf8mb4'.format(db_02)

# 积分总结sql
point_summary_query = '''select 
                    DATE_FORMAT(`create_date`,'%%Y-%%m-%%d') as '日期', 
                    abs(sum(`change`))/100 as '积分充值智能校园(元)' 
                    FROM `point_trace` 
                    WHERE `long_describe` = '智能校园' and `short_describe` like '抵扣%%' 
                    and `create_date` >= '{0}' and DATE_FORMAT(`create_date`,'%%Y-%%m-%%d') <= '{1}' 
                    and `type` = 2 and `login_id` != '18321593357' 
                    group by DATE_FORMAT(`create_date`, '%%Y-%%m-%%d') '''

# 折扣券 & 代金券 总结sql
deduction_summary_query = '''SELECT 
                    DATE_FORMAT(`user_discount_detail`.`create_time`, '%%Y-%%m-%%d') as '日期', 
                    SUM(`user_discount_detail`.`reduce_amount`) as '卡券抵扣智能校园(元)' 
                    FROM `user_discount_detail` 
                    LEFT JOIN user_discount on user_discount_detail.user_discount_id= user_discount.id 
                    WHERE user_discount_detail.create_time >= '{0}' and DATE_FORMAT(`user_discount_detail`.`create_time`, '%%Y-%%m-%%d') <= '{1}' 
                    and `user_discount_detail`.`type`=2 and `user_discount`.`scope` ='school'
                    group by DATE_FORMAT(`user_discount_detail`.`create_time`, '%%Y-%%m-%%d') '''

# 订单总结sql
order_summary_query = '''SELECT DATE_FORMAT(`created_date`,  '%%Y-%%m-%%d') as '日期', 
                    count(1) as '用户消费次数(次)' , 
                    abs(sum(`point`))/100 as '用户消费总金额(元)'
                    FROM `order_v1` 
                    WHERE `created_date` >= '{0}' and DATE_FORMAT(`created_date`,  '%%Y-%%m-%%d') <= '{1}'
                    and `specific_type` = 4 and `type` = 2 and `flow_number` != '18321593357' 
                    group by DATE_FORMAT(`created_date`, '%%Y-%%m-%%d') '''
# 订单明细sql
order_trace_query = '''SELECT `id`,abs(`point`)/100 as 'amount',`content`, DATE_FORMAT(`created_date`,  '%%Y-%%m-%%d') as `created_date` 
                    FROM `order_v1` 
                    WHERE `created_date` >= '{0}' and DATE_FORMAT(`created_date`, '%%Y-%%m-%%d') <= '{1}' 
                    and `specific_type` = 4 and `type` = 2 and `flow_number` != '18321593357' '''

# 积分
def get_point_summary(start_date, end_date):
    try:
        engine = db.create_engine(mysql_asset_conn_str)
        connection = engine.connect()
        
        df = pd.read_sql_query(point_summary_query.format(start_date, end_date), connection, index_col='日期')
    except:
        print("读取数据错误")
        raise "读取数据错误"
    connection.close()
    return df

# 卡券 (代金券+折扣券) 不支持2018-11-08之前的数据
def get_deduction_summary(start_date, end_date):
    try:
        engine = db.create_engine(mysql_discount_conn_str)
        connection = engine.connect()
        
        df = pd.read_sql_query(deduction_summary_query.format(start_date, end_date), connection, index_col='日期')
    except:
        print("读取数据错误")
        raise "读取数据错误"
    connection.close()
    return df

# 订单
def get_order_summary(start_date, end_date):
    try:
        engine = db.create_engine(mysql_order_conn_str)
        connection = engine.connect()
        
        df = pd.read_sql_query(order_summary_query.format(start_date, end_date), connection, index_col='日期')
    except:
        print("读取数据错误")
        raise "读取数据错误"
    connection.close()
    return df

# 订单明细
def get_order_trace(start_date, end_date):
    try:
        engine = db.create_engine(mysql_order_conn_str)
        connection = engine.connect()
        
        df = pd.read_sql_query(order_trace_query.format(start_date, end_date), connection)
    except:
        print("读取数据错误")
        raise "读取数据错误"
    connection.close()
    return df

# 写入数据库
def save_elimination_data(table_name, df):
    try:
        engine = db.create_engine(mysql_elimination_conn_str)
        connection = engine.connect()

        df.to_sql(table_name, con=connection, if_exists='append', index=False)
    except:
        print("写入数据错误")
        raise "写入数据错误"
    connection.close()


# In[67]:


# 积分统计
point_df = get_point_summary(start_date, end_date)
# 卡券统计
deduction_df = get_deduction_summary(start_date, end_date)
# 订单统计
order_df = get_order_summary(start_date, end_date)
# 订单明细
# order_trace_df = get_order_trace(start_date, end_date)


# In[ ]:


# ----------------------------积分卡券使用总结----------------------------
# 多数据合并 订单+积分+卡券
concat_df = pd.concat([order_df, point_df, deduction_df], axis=1)

# 将NaN数据改为0
concat_df.fillna(value=0, inplace=True)

# 增加字段，计算清帐金额
concat_df['需要清账金额(元)'] = concat_df['积分充值智能校园(元)'] + concat_df['卡券抵扣智能校园(元)']

# 报表数据 横向展示, 数据反转
# concat_df = concat_df.T


# In[ ]:


# 更改数据所需字段名称
concat_df.reset_index(inplace=True)
concat_df.columns = ['date','consumption_number','consumption_amount','top_up_amount','deduction_amount','elimination_amount']

# 补充没有缺少的日期数据
d = start_date
delta = timedelta(days=1)
while d <= end_date:
    if len(concat_df.loc[concat_df['date'] == d.strftime("%Y-%m-%d")]) == 0:
        df = pd.DataFrame(columns=['date','consumption_number','consumption_amount','top_up_amount','deduction_amount','elimination_amount'], data=[[d.strftime("%Y-%m-%d"), 0, 0, 0, 0, 0]])
        concat_df = concat_df.append(df)
    d += delta

# 排序
concat_df.sort_values('date', inplace=True)
concat_df['created_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
concat_df['modify_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# 积分卡券使用总结 -> 写入数据库
try:
    save_elimination_data('use_asset_trace', concat_df)
except BaseException:
    logging.error('-----  积分卡券使用总结,写入数据库错误。有重复计算的数据，日期不可重复 start_date={}, end_date={}-----'.format(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))


# In[96]:


# ----------------------------商户打款总结----------------------------

# 计算商户打款比例
# def get_merchent(df):
#     try:
#         if df['content'] is not None:
#             json_data = json.loads(df['content'])
#             if 'deviceMerchant' in json_data:
#                 return json_data['deviceMerchant']
#     except ValueError:
#         return '其他商户'
#     return '其他商户'

# # 获取json中的商户号
# order_trace_df['商户'] = order_trace_df.apply(get_merchent, axis=1)

# # df1 = order_trace_df.groupby('商户').sum()['amount']
# # df2 = order_trace_df['商户'].value_counts()

# # df1.name = '订单额(元)'
# # df2.name = '订单数(次)'

# # order_trace_df = pd.concat([df1, df2], axis=1)

# order_trace_df.columns = ['id', '金额', 'content', '日期', '商户']
# group_df = order_trace_df.groupby(['日期','商户']).sum()['金额']
# group_df = group_df.to_frame().reset_index().set_index('日期')


# In[97]:


# ----------------------------商户打款总结----------------------------

# 默认统一商户
# merchant_df = concat_df.drop(columns=['consumption_number','consumption_amount','top_up_amount', 'deduction_amount'])
# merchant_df['merchant_name'] = 'fnvalley_test'
# merchant_df.columns = ['date','amount','created_date','modify_date','merchant_name']
# merchant_df = merchant_df[merchant_df['amount'] > 0]

# 商户打款总结 -> 写入数据库
# save_elimination_data('elimination_trace', merchant_df)


# In[ ]:


# ----------------------------商户打款总结----------------------------

# 写死打款商户 以及打款比例 13772135611:暂定总额4/5, 13022967817:暂定1/5

# 13772135611:暂定总额4/5
merchant_df_01 = concat_df.drop(columns=['consumption_number','consumption_amount','top_up_amount', 'deduction_amount'])
merchant_df_01['merchant_name'] = '刘胜'
merchant_df_01.columns = ['date','amount','created_date','modify_date','merchant_name']
merchant_df_01['amount'] = merchant_df_01['amount'] * 0.8
merchant_df_01 = merchant_df_01.round(2)
merchant_df_01 = merchant_df_01[merchant_df_01['amount'] > 0]

# 13022967817:暂定1/5
merchant_df_02 = concat_df.drop(columns=['consumption_number','consumption_amount','top_up_amount', 'deduction_amount'])
merchant_df_02['merchant_name'] = '杨新立'
merchant_df_02.columns = ['date','amount','created_date','modify_date','merchant_name']
merchant_df_02['amount'] = merchant_df_02['amount'] * 0.2
merchant_df_02 = merchant_df_02.round(2)
merchant_df_02 = merchant_df_02[merchant_df_02['amount'] > 0]

# 商户打款总结 -> 写入数据库
try:
    save_elimination_data('elimination_trace', merchant_df_01)
except BaseException:
    logging.error('-----  商户打款总结,写入数据库错误。有重复计算的数据，日期不可重复  商户:刘胜, start_date={}, end_date={}-----'.format(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))

try:
    save_elimination_data('elimination_trace', merchant_df_02)
except BaseException:
    logging.error('-----  商户打款总结,写入数据库错误。有重复计算的数据，日期不可重复  商户:杨新立, start_date={}, end_date={}-----'.format(start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")))


# In[ ]:


logging.info('==========================  销帐计算 end  ==========================')


# In[ ]:




