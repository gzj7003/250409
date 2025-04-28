import os
import re
import base64
import cv2
import requests
import concurrent.futures
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# 常量配置
CONFIG = {
    "input_dir": "udpsc",
    "output_dir": "txt_files",
    "request_headers": {
        "referer": "https://www.baidu.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
        "cookie": os.getenv("FOFA_COOKIE", "")  # 从环境变量读取cookie
    },
    "isp_mapping": {
        ("北京", "联通"): {"isp_en": "cucc", "org": "China Unicom Beijing Province Network"},
        ("", "联通"): {"isp_en": "cucc", "org": "CHINA UNICOM China169 Backbone"},
        ("", "电信"): {"org": "Chinanet", "isp_en": "ctcc"},
        ("", "移动"): {"org": "China Mobile communications corporation", "isp_en": "cmcc"}
    },
    "timeout": 5,
    "max_retries": 3,
    "max_workers": 5
}

def setup_dirs():
    """创建必要的目录结构"""
    os.makedirs(CONFIG["input_dir"], exist_ok=True)
    os.makedirs(CONFIG["output_dir"], exist_ok=True)

def get_isp_info(province, isp):
    """获取ISP对应的组织信息"""
    for (p, i), info in CONFIG["isp_mapping"].items():
        if (p == province or p == "") and i == isp:
            return info
    return {"org": "", "isp_en": ""}

def validate_stream(url, timeout=5):
    """验证视频流有效性"""
    try:
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            return width > 0 and height > 0
        return False
    except Exception as e:
        print(f"视频流验证异常：{str(e)}")
        return False

def process_file(province_isp):
    """处理单个省份运营商文件"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    province, isp = province_isp.split('_')
    isp_info = get_isp_info(province, isp)
    
    if not isp_info.get("org"):
        print(f"{current_time} [{province}{isp}] 未找到匹配的ISP信息")
        return

    try:
        with open(f'{CONFIG["input_dir"]}/{province_isp}.txt', 'r', encoding='utf-8') as f:
            data = f.read().strip()
            if not data:
                return

        mcast = data.split("rtp://")[1].split()[0] if "rtp://" in data else None
        if not mcast:
            return

        search_txt = base64.b64encode(
            f'\"udpxy\" && country=\"CN\" && region=\"{province}\" && org=\"{isp_info["org"]}\"'.encode()
        ).decode()
        
        result_urls = set()
        for _ in range(CONFIG["max_retries"]):
            try:
                response = requests.get(
                    f'https://fofa.info/result?qbase64={search_txt}',
                    headers=CONFIG["request_headers"],
                    timeout=CONFIG["timeout"]
                )
                result_urls = set(re.findall(r"http://\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+", response.text))
                if result_urls:
                    break
            except requests.RequestException:
                continue

        valid_urls = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG["max_workers"]) as executor:
            futures = {
                executor.submit(
                    validate_stream,
                    f"{url}/rtp/{mcast}",
                    CONFIG["timeout"]
                ): url for url in result_urls
            }
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    valid_urls.append(futures[future])

        if valid_urls:
            new_data = "\n".join([data.replace("rtp://", f"{url}/rtp/") for url in valid_urls])
            suzhou_channels = """
# 苏州新闻综合
苏州新闻综合,https://live-auth.51kandianshi.com/szgd/csztv1.m3u8
# 苏州社会经济
苏州社会经济,https://live-auth.51kandianshi.com/szgd/csztv2.m3u8
# 苏州文化生活
苏州文化生活,https://live-auth.51kandianshi.com/szgd/csztv3.m3u8
# 苏州生活资讯
苏州生活资讯,https://live-auth.51kandianshi.com/szgd/csztv5.m3u8
# 苏州4K
苏州4K,https://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8
"""
            output_path = f'{CONFIG["output_dir"]}/{province}{isp}.txt'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(new_data + suzhou_channels)
            print(f"{current_time} 成功生成播放列表：{output_path}")

    except Exception as e:
        print(f"{current_time} 处理 {province_isp} 时发生错误：{str(e)}")

def main():
    setup_dirs()
    
    provinces_isps = [
        name.rsplit('.', 1)[0] for name in os.listdir(CONFIG["input_dir"])
        if name.endswith('.txt') and name.count('_') == 1
    ]
    
    print(f"本次查询：{provinces_isps} 的组播节目")
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(process_file, provinces_isps)
    
    print('节目表制作完成！文件输出在 txt_files 目录下！')

if __name__ == "__main__":
    main()
