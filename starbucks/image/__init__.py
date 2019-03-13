
# 下载图片
import urllib

def download_image(url, file_path):
    response = urllib.request.urlopen(url)
    pic = response.read()
    with open(file_path, 'wb') as f:
        f.write(pic)
