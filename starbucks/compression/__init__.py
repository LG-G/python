# -*- coding: utf-8 -*-



# 压缩
import zipfile
import os

# 压缩文件
# def zip_files(files, zip_name):
#     zip = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
#     for file in files:
#         print ('compressing', file)
#         zip.write(file)
#     zip.close()
#     print ('compressing finished')

# 压缩文件夹
def make_zip(source_dir, output_filename):
    zipf = zipfile.ZipFile(output_filename, 'w')
    pre_len = len(os.path.dirname(source_dir))
    for parent, dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            pathfile = os.path.join(parent, filename)
            arcname = pathfile[pre_len:].strip(os.path.sep)   #相对路径
            zipf.write(pathfile, arcname)
    zipf.close()
