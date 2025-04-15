import os
import requests
import re
import base64
import cv2
import datetime
import time
import random
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# 设置随机用户代理和延迟
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
]

def get_random_headers():
    return {
        "referer": "https://www.google.com/",
        "user-agent": random.choice(USER_AGENTS),
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.5",
        "accept-encoding": "gzip, deflate, br",
        "connection": "keep-alive",
        "upgrade-insecure-requests": "1",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "cache-control": "max-age=0"
    }

files = os.listdir('udpsh')
files_name = []

for file in files:
    name, extension = os.path.splitext(file)
    files_name.append(name)

provinces_isps = [name for name in files_name if name.count('_') == 1]

print(f"本次查询：{provinces_isps}的组播节目") 

keywords = []

for province_isp in provinces_isps:
    try:
        with open(f'udpsh/{province_isp}.txt', 'r', encoding='utf-8') as file:
            lines = file.readlines()
            lines = [line.strip() for line in lines if line.strip()]

        if lines:
            first_line = lines[0]
            if "rtp://" in first_line:
                mcast = first_line.split("rtp://")[1].split(" ")[0]
                keywords.append(province_isp + "_" + mcast)
    except FileNotFoundError:
        print(f"文件 '{province_isp}.txt' 不存在. 跳过此文件.")

for keyword in keywords:
    province, isp, mcast = keyword.split("_")

    if province == "北京" and isp == "联通":
        isp_en = "cucc"
        org = "China Unicom Beijing Province Network"
    elif isp == "联通":
        isp_en = "cucc"
        org = "CHINA UNICOM China169 Backbone"
    elif isp == "电信":
        org = "China Telecom Group"
        isp_en = "ctcc"
    elif isp == "移动":
        org = "China Mobile communications corporation"
        isp_en = "cmcc"
        
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timeout_cnt = 0
    result_urls = set() 
    
    while len(result_urls) == 0 and timeout_cnt <= 5:
        try:
            # 添加随机延迟
            time.sleep(random.uniform(1, 3))
            
            search_url = 'https://fofa.info/result?qbase64='
            search_txt = f'\"udpxy\" && country=\"CN\" && region=\"{province}\" && org=\"{org}\"'
            bytes_string = search_txt.encode('utf-8')

            search_txt = base64.b64encode(bytes_string).decode('utf-8')
            search_url += search_txt
            print(f"{current_time} 查询运营商 : {province}{isp} ，查询网址 : {search_url}")

            response = requests.get(search_url, headers=get_random_headers(), timeout=10)
            response.raise_for_status()

            html_content = response.text
            html_soup = BeautifulSoup(html_content, "html.parser")

            pattern = r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+"
            urls_all = re.findall(pattern, html_content)

            result_urls = set(urls_all)
            print(f"{current_time} 找到 {len(result_urls)} 个URL")

            valid_ips = []

            for url in result_urls:
                try:
                    video_url = url + "/rtp/" + mcast
                    print(f"正在测试 {video_url}...")
                    
                    # 添加测试前的延迟
                    time.sleep(random.uniform(0.5, 1.5))
                    
                    cap = cv2.VideoCapture(video_url)

                    if not cap.isOpened():
                        print(f"{current_time} {video_url} 无效")
                    else:
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        print(f"{current_time} {video_url} 的分辨率为 {width}x{height}")

                        if width > 0 and height > 0:
                            valid_ips.append(url)

                        cap.release()
                except Exception as e:
                    print(f"测试 {url} 时出错: {str(e)}")
                    continue
                    
            if valid_ips:
                update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rtp_filename = f'udpsh/{province}_{isp}.txt'
                with open(rtp_filename, 'r', encoding='utf-8') as file:
                    data = file.read()
                
                txt_filename = f'txt_files/{province}{isp}.txt'
                with open(txt_filename, 'w') as new_file:
                    # 添加更新时间头
                    new_file.write(f"# 更新时间: {update_time}\n")
                    new_file.write(f"# 来源: {province}{isp} UDPXY转播\n\n")
                    
                    # 原始内容转换
                    for url in valid_ips:
                        new_data = data.replace("rtp://", f"{url}/rtp/")
                        new_file.write(new_data)
                    
                    # 新增定制内容
                    new_file.write("\n# 苏州新闻综合\n")
                    new_file.write("苏州新闻综合,https://live-auth.51kandianshi.com/szgd/csztv1.m3u8\n")
                    new_file.write("\n# 苏州社会经济\n")
                    new_file.write("苏州社会经济,https://live-auth.51kandianshi.com/szgd/csztv2.m3u8\n")
                    new_file.write("\n# 苏州文化生活\n")
                    new_file.write("苏州文化生活,https://live-auth.51kandianshi.com/szgd/csztv3.m3u8\n")
                    new_file.write("\n# 苏州生活资讯\n")
                    new_file.write("苏州生活资讯,https://live-auth.51kandianshi.com/szgd/csztv5.m3u8\n")
                    new_file.write("\n# 苏州4K\n")               
                    new_file.write("苏州4K,https://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8\n")
                       
                print(f'已生成播放列表，保存至 {txt_filename}')

        except requests.exceptions.RequestException as e:
            timeout_cnt += 1
            print(f"{current_time} [{province}] 请求发生错误: {str(e)}，异常次数：{timeout_cnt}")
            if timeout_cnt <= 3:
                # 出错后增加延迟
                time.sleep(random.uniform(5, 10))
                continue
            else:
                print(f"{current_time} 搜索IPTV频道源[{province}{isp}]，错误次数过多：{timeout_cnt} 次，停止处理")
                break
        except Exception as e:
            print(f"{current_time} 发生未知错误: {str(e)}")
            timeout_cnt += 1
            if timeout_cnt <= 3:
                time.sleep(random.uniform(5, 10))
                continue
            else:
                print(f"{current_time} 未知错误次数过多，停止处理")
                break

print('节目表制作完成！ 文件输出在 txt_files 目录下！')
