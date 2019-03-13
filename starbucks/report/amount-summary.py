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

# #导入绘图工具
# import matplotlib.pyplot as plt
# #一般作为机器学习绘图用, 但是也能绘出更cool的图
# import seaborn as sns

#mysql 数据源工具
import sqlalchemy as db

#系统及命令行
import sys

from datetime import datetime, date, timedelta
import json

#发邮件
from starbucks import mail

# #行内xi
# %matplotlib inline


# In[2]:


# 数据库链接：root:82f12dbf497b@10.10.0.215
db_01 = sys.argv[1]
db_02 = sys.argv[2]
# 日期 2018-11-11
start_date = sys.argv[3]
if len(sys.argv) > 4:
    end_date = sys.argv[4]
else:
    end_date = str(sys.argv[3]) + ' 23:59:59'


# In[3]:


mysql_asset_conn_str = 'mysql+pymysql://{}/asset_service?charset=utf8mb4'.format(db_01)
mysql_discount_conn_str = 'mysql+pymysql://{}/discount_tickets_service?charset=utf8mb4'.format(db_02)
mysql_order_conn_str = 'mysql+pymysql://{}/order_service?charset=utf8mb4'.format(db_02)

# 积分总结sql
point_summary_query = '''select 
                    DATE_FORMAT(`create_date`,'%%Y-%%m-%%d') as '日期', 
                    abs(sum(`change`))/100 as '积分充值金额(元)' 
                    FROM `point_trace` 
                    WHERE `long_describe` = '智能校园' and `short_describe` like '抵扣%%' 
                    and `create_date` >= '{0}' and `create_date` <= '{1}' 
                    and `type` = 2 and `login_id` != '18321593357' 
                    group by DATE_FORMAT(`create_date`, '%%Y-%%m-%%d') '''
# 折扣券总结sql
discount_summary_query = '''SELECT 
                    date_format(`user_discount_detail`.`create_time`, '%%Y-%%m-%%d') as '日期', 
                    sum((10-user_discount.discount_name)/10 * user_discount_detail.order_amount) as '折扣券抵扣金额(元)' 
                    FROM user_discount_detail LEFT JOIN user_discount on user_discount_detail.user_discount_id= user_discount.id
                    where user_discount_detail.discriminator = 'discount' 
                    and user_discount_detail.create_time >= '{0}' and user_discount_detail.create_time <= '{1}' 
                    and user_discount_detail.type=2 and user_discount.`scope` ='school' 
                    and user_discount_detail.login_id != 18321593357 
                    GROUP BY date_format(`user_discount_detail`.`create_time`, '%%Y-%%m-%%d') '''
# 代金券总结sql
deductible_summary_query = '''SELECT 
                    DATE_FORMAT(`user_discount_detail`.`create_time`, '%%Y-%%m-%%d') as '日期', 
                    sum(IF(user_discount_detail.order_amount >= user_discount.deductible_amount, user_discount.deductible_amount, user_discount_detail.order_amount)) as '优惠券抵扣金额(元)' 
                    FROM user_discount_detail LEFT JOIN user_discount on user_discount_detail.user_discount_id= user_discount.id 
                    where user_discount_detail.discriminator = 'deductible' 
                    and user_discount_detail.create_time >= '{0}' and user_discount_detail.create_time <= '{1}' 
                    and user_discount_detail.type=2 and user_discount.`scope` ='school' 
                    and user_discount_detail.login_id != 18321593357
                    group by DATE_FORMAT(`user_discount_detail`.`create_time`, '%%Y-%%m-%%d') '''
# 订单总结sql
order_summary_query = '''SELECT DATE_FORMAT(`created_date`,  '%%Y-%%m-%%d') as '日期', 
                    abs(sum(`point`))/100 as '订单消费金额(元)', 
                    count(1) as '订单数量(次)' 
                    FROM `order_v1` 
                    WHERE `created_date` >= '{0}' and `created_date` <= '{1}'
                    and `specific_type` = 4 and `type` = 2 and `flow_number` != '18321593357' 
                    group by DATE_FORMAT(`created_date`, '%%Y-%%m-%%d') '''
# 订单明细sql
order_trace_query = '''SELECT `id`,abs(`point`)/100 as 'amount',`content`,`created_date`
                    FROM `order_v1` 
                    WHERE `created_date` >= '{0}' and `created_date` <= '{1}' 
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

# 折扣券
def get_discount_summary(start_date, end_date):
    try:
        engine = db.create_engine(mysql_discount_conn_str)
        connection = engine.connect()
        
        df = pd.read_sql_query(discount_summary_query.format(start_date, end_date), connection, index_col='日期')
    except:
        print("读取数据错误")
        raise "读取数据错误"
    connection.close()
    return df

# 代金券
def get_deductible_summary(start_date, end_date):
    try:
        engine = db.create_engine(mysql_discount_conn_str)
        connection = engine.connect()
        
        df = pd.read_sql_query(deductible_summary_query.format(start_date, end_date), connection, index_col='日期')
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


# In[4]:


# 积分统计
point_df = get_point_summary(start_date, end_date)
# 折扣券统计
deductible_df = get_deductible_summary(start_date, end_date)
# 代金券统计
discount_df = get_discount_summary(start_date, end_date)
# 订单统计
order_df = get_order_summary(start_date, end_date)
# # 订单明细
# order_trace_df = get_order_trace(start_date, end_date)


# In[136]:


# 多数据合并
concat_df = pd.concat([order_df, point_df, deductible_df, discount_df], axis=1)

# 将NaN数据改为0
concat_df.fillna(value=0, inplace=True)

# 增加字段
concat_df['补贴总额(元)'] = concat_df['积分充值金额(元)'] + concat_df['折扣券抵扣金额(元)'] + concat_df['优惠券抵扣金额(元)']

# 整理导入Excel数据顺序
excel_df = ['积分充值金额(元)', '折扣券抵扣金额(元)', '优惠券抵扣金额(元)', '订单数量(次)', '订单消费金额(元)', '补贴总额(元)']
concat_df = concat_df[excel_df]

# # 计算总计
# total_ser = concat_df.sum()
# total_ser.name = '总计'

# # 添加总计
# total_df = pd.DataFrame(total_ser)
# concat_df = concat_df.append(total_df.T)

# 每日报表数据 横向展示, 数据反转
concat_df = concat_df.T


# In[137]:


# def get_merchent(df):
#     try:
#         if df['content'] is not None:
#             json_data = json.loads(df['content'])
#             if 'deviceMerchant' in json_data:
#                 return json_data['deviceMerchant']
#     except ValueError:
#         return '其他商户'
#     return '其他商户'

# # 提出商户号
# order_trace_df['商户'] = order_trace_df.apply(get_merchent, axis=1)

# df1 = order_trace_df.groupby('商户').sum()['amount']
# df2 = order_trace_df['商户'].value_counts()

# df1.name = '订单额(元)'
# df2.name = '订单数(次)'

# order_trace_df = pd.concat([df1, df2], axis=1)


# In[138]:


# 生成 excel
writer = pd.ExcelWriter('/tmp/{}.xlsx'.format(start_date))

concat_df.to_excel(writer, sheet_name='总揽', index_label='日期')
writer.save()

# order_trace_df.to_excel(writer, sheet_name='商户积分补偿分配情况', index_label='商户名')
# writer.save()


# In[141]:


# 发送带附件的邮件
recipient = 'spark.zhu@zan-qian.com'

mail.send_mail_attachment(file_path='/tmp/{}.xlsx'.format(start_date), file_name='统计.xlsx', recipient=recipient, subject="统计报表")

