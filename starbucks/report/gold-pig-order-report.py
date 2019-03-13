#!/usr/bin/env python
# coding: utf-8

# # 安装Mysql 驱动 
# 
# ```python
# pip install sqlalchemy
# ```

# In[41]:


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
#发邮件
from starbucks import mail

logging.getLogger().setLevel(logging.INFO)


# In[42]:


logging.info('------------ datetime_now : {}------------'.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
logging.info('==========================  金猪活动订单记录 start  ==========================')

ACCESS_TOKEN="4f55964d-d361-44fe-94d8-2f2eaedce16e"
headers = {'Authorization': 'Bearer {}'.format(ACCESS_TOKEN), 'Content-Type': 'application/json'}

# env = 'prod'
# recipient = 'jiangmin@zan-qian.com'
# start_date = datetime.strptime('2019-02-01', "%Y-%m-%d")
# end_date = datetime.strptime('2019-02-28', "%Y-%m-%d")
# sys.argv = ["", "test", "bell.qiu@zan-qian.com", "2019-02-01", "2019-02-28"]

# 环境
env = sys.argv[1]
# 邮件收件人
recipient = sys.argv[2]
# 开始时间
start_date = datetime.strptime(sys.argv[3], "%Y-%m-%d")
# 结束时间
end_date = datetime.strptime(sys.argv[3], "%Y-%m-%d")

if len(sys.argv) > 4:
    end_date = datetime.strptime(sys.argv[4], "%Y-%m-%d")

if str(env) == 'test':
    get_user_address_url="http://testgate.zan-qian.com/profile-service/2.0.0/extra_profile/queryDeliveryInfo"
    db_01 = 'root:82f12dbf497b@10.10.0.215'
    db_02 = 'root:82f12dbf497b@10.10.0.215'
elif str(env) == 'prod':
    get_user_address_url="http://gateway.zan-qian.com/profile-service/2.0.0/extra_profile/queryDeliveryInfo"
    db_01 = 'cityzone:Hellowrold@123@cityzone-service.mysql.rds.aliyuncs.com:3306'
    db_02 = 'cityzone:Hellowrold@123@cityzone-resources.mysql.rds.aliyuncs.com:3306'
else:
    get_user_address_url="http://testgate.zan-qian.com/profile-service/2.0.0/extra_profile/queryDeliveryInfo"
    db_01 = 'root:82f12dbf497b@10.10.0.215'
    db_02 = 'root:82f12dbf497b@10.10.0.215'

# log 参数信息
logging.info('-----  env={}, start_date={}, end_date={}  -----'.format(env, start_date, end_date))
logging.info('-----  get_user_address_url={}  -----'.format(get_user_address_url))
logging.info('-----  db_01={}  -----'.format(db_01))
logging.info('-----  db_02={}  -----'.format(db_02))


# In[43]:


mysql_order_conn_str = 'mysql+pymysql://{}/order_service?charset=utf8mb4'.format(db_02)

# 订单记录sql
order_trace_query = '''select t1.order_no,t1.login_id,t2.sku_no,t1.`status` 
                    from trade_order t1 
                    left join order_sku t2 on t1.order_no = t2.order_no 
                    WHERE t1.`create_date` >= '{0}' and DATE_FORMAT(t1.`create_date`, '%%Y-%%m-%%d') <= '{1}' 
                    and t1.`specific_type` = 28 '''

# 订单记录
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


# In[45]:


mysql_singin_conn_str = 'mysql+pymysql://{}/task_service?charset=utf8mb4'.format(db_01)

delta_days = (end_date - start_date).days + 1
# 每天签到的人的统计sql
signin_query = '''select login_id, c from (SELECT login_id, count(1) as c FROM signin 
                    WHERE create_date >= '{0}' and DATE_FORMAT(`create_date`, '%%Y-%%m-%%d') <= '{1}' GROUP BY login_id) 
                    a where c >= {2}'''.format(start_date, end_date, delta_days)
print(signin_query)

# 每天签到的人
def get_sigin_df(start_date, end_date):
    try:
        engine = db.create_engine(mysql_singin_conn_str)
        connection = engine.connect()
        
        df = pd.read_sql_query(signin_query, connection)
        df.columns=['签到用户','签到次数']
    except:
        print("读取数据错误")
        raise "读取数据错误"
    connection.close()
    return df['签到用户']

signin_df = get_sigin_df(start_date, end_date)


# In[46]:


# 订单记录
order_trace_df = get_order_trace(start_date, end_date)

order_trace_df.loc[order_trace_df['sku_no'] == '1021_promotion_exchange_point_200', 'sku_no'] = '200积分'
order_trace_df.loc[order_trace_df['sku_no'] == '1021_promotion_exchange_deductible_4', 'sku_no'] = '趣谷APP洗衣券'
order_trace_df.loc[order_trace_df['sku_no'] == '1021_promotion_exchange_bestv_3_month', 'sku_no'] = 'BesTV会员季卡'
order_trace_df.loc[order_trace_df['sku_no'] == '1021_promotion_exchange_water_frost', 'sku_no'] = '朵薇璐HI室友活氧沁水霜'
order_trace_df.loc[order_trace_df['sku_no'] == '1021_promotion_exchange_bluetooth_headset', 'sku_no'] = '飞利浦蓝牙音响'
order_trace_df.loc[order_trace_df['sku_no'] == '1021_promotion_exchange_golden_pig', 'sku_no'] = 'popking金猪'
order_trace_df.loc[order_trace_df['status'] == 'wait_seller_send_goods', 'status'] = '等待发货'
order_trace_df.loc[order_trace_df['status'] == 'trade_finished', 'status'] = '已完结'

# 查询用户收获地址
def get_user_address(df):
    request_param = [df['login_id']]
    response = requests.post(url=get_user_address_url, json=request_param, headers=headers)
    print(response.content)
    address_json = json.loads(response.content).get('data')[0]
    print(address_json)
    if address_json.get('deliveryName') is not None:
        df['收货人姓名'] = address_json.get('deliveryName')
        df['收货人电话'] = address_json.get('deliveryPhone')
        df['收货人地址'] = address_json.get('deliveryAddress')
    else:
        df['收货人姓名'] = ''
        df['收货人电话'] = ''
        df['收货人地址'] = ''
    return df

order_trace_df = order_trace_df.apply(get_user_address, axis=1)
order_trace_df.fillna(value='', inplace=True)
order_trace_df.columns = ['订单号','兑换用户','兑换产品','订单状态','收货人姓名','收货人电话','收货人地址']


# In[47]:


# 生成 excel
writer = pd.ExcelWriter('/tmp/gold-ping.xlsx')
order_trace_df.to_excel(writer, sheet_name='金猪活动兑换明细', index=False)
signin_df.to_excel(writer, sheet_name='金猪活动签到满28天的名单', index=False)
writer.save()


# In[ ]:


# 发送带附件的邮件
mail.send_mail_attachment(file_path='/tmp/gold-ping.xlsx', file_name='金猪活动兑换明细.xlsx', recipient=recipient, subject="金猪活动兑换明细")


# In[ ]:


logging.info('==========================  金猪活动订单记录 end  ==========================')

