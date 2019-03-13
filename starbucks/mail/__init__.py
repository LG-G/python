# -*- coding: utf-8 -*-



#发邮件
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

email_host = 'smtp.exmail.qq.com'
send_user = 'noreply@zan-qian.com'
password = 'Jlzmht2Bxz'
# recipient = 'spark.zhu@zan-qian.com'

# 发送带附件的邮件
def send_mail_attachment(file_path, file_name='文件名.txt', subject='', content='', recipient='spark.zhu@zan-qian.com'):
    try:
        msg = MIMEMultipart()
        msg['from'] = '趣谷<{}>'.format(send_user)
        msg['to'] = recipient
        msg['subject'] = subject
        content = content
        txt = MIMEText(content, 'plain', 'utf-8')
        msg.attach(txt)

        # 添加附件
        part = MIMEApplication(open(file_path,'rb').read())
        part.add_header('Content-Disposition', 'attachment', filename=('gbk', '', file_name))
        msg.attach(part)

        smtp = smtplib.SMTP_SSL(email_host)
        smtp.connect(email_host)
        smtp.login(send_user, password)
        smtp.sendmail(send_user, recipient.split(','), str(msg))
        smtp.quit()
    except :
        print("邮件发送失败")
        raise "邮件发送失败"


# 发送带多个附件的邮件
def send_mail_attachments(file_path, file_name='文件名.txt', subject='', content='', recipient='spark.zhu@zan-qian.com'):
    try:
        msg = MIMEMultipart()
        msg['from'] = '趣谷<{}>'.format(send_user)
        msg['to'] = recipient
        msg['subject'] = subject
        content = content
        txt = MIMEText(content, 'plain', 'utf-8')
        msg.attach(txt)

        # 添加附件
        for index,val in enumerate(file_path):
            part = MIMEApplication(open(val,'rb').read())
            part.add_header('Content-Disposition', 'attachment', filename=('gbk', '', file_name[index]))
            msg.attach(part)

        smtp = smtplib.SMTP_SSL(email_host)
        smtp.connect(email_host)
        smtp.login(send_user, password)
        smtp.sendmail(send_user, recipient.split(','), str(msg))
        smtp.quit()
    except :
        print("邮件发送失败")
        raise "邮件发送失败"
