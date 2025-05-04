import requests
import os
from pathlib import Path

def generate_live_source():
    original_urls = [
        "https://raw.githubusercontent.com/zhuxinfu88/tvlist/main/txt_files/Susa.txt",
        "https://raw.githubusercontent.com/zhuxinfu88/tvlist/main/txt_files/Susaw.txt"
    ]

    template_channels = [
        "CCTV1", "CCTV2", "CCTV3", "CCTV4", "CCTV5", "CCTV6", "CCTV7", "CCTV8",
        "CCTV9", "CCTV10", "CCTV11", "CCTV12", "CCTV13", "CCTV14", "CCTV15",
        "湖南卫视", "浙江卫视", "东方卫视", "北京卫视", "江苏卫视", "兵团卫视"
    ]

    suzhou_sources = [
        "苏州新闻综合,https://live-auth.51kandianshi.com/szgd/csztv1.m3u8$江苏苏州地方",
        "苏州社会经济,https://live-auth.51kandianshi.com/szgd/csztv2.m3u8$江苏苏州地方",
        "苏州文化生活,https://live-auth.51kandianshi.com/szgd/csztv3.m3u8$江苏苏州地方",
        "苏州生活资讯,https://live-auth.51kandianshi.com/szgd/csztv5.m3u8$江苏苏州地方",
        "苏州4K,https://live-auth.51kandianshi.com/szgd/csztv4k_hd.m3u8$江苏苏州地方"
    ]

    try:
        # 创建目录
        output_dir = Path("txt_files")
        output_dir.mkdir(exist_ok=True)

        # 合并源内容
        combined_content = []
        for url in original_urls:
            response = requests.get(url)
            response.raise_for_status()
            combined_content.extend(response.text.strip().split('\n'))

        # 添加苏州台并过滤频道
        filtered_content = []
        seen_channels = set()
        
        for line in combined_content + suzhou_sources:
            if not line.strip():
                continue
            name_part = line.split(',', 1)[0]
            
            # 频道过滤逻辑
            if any(channel in name_part for channel in template_channels) \
               or "苏州" in name_part:
                if name_part not in seen_channels:
                    seen_channels.add(name_part)
                    filtered_content.append(line)

        # 保存文本文件
        txt_path = output_dir / "Susaw-sa.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(filtered_content))

        # 生成M3U文件
        m3u_content = ["#EXTM3U"]
        for line in filtered_content:
            if ',' in line:
                name, url_part = line.split(',', 1)
                m3u_content.append(f"#EXTINF:-1,{name}")
                m3u_content.append(url_part.split('$')[0])

        m3u_path = output_dir / "Susaw-sa.m3u"
        with open(m3u_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(m3u_content))

        print(f"成功生成文件: {txt_path} 和 {m3u_path}")

    except requests.RequestException as e:
        print(f"请求错误: {str(e)}")
        exit(1)
    except Exception as e:
        print(f"运行时错误: {str(e)}")
        exit(1)

if __name__ == "__main__":
    generate_live_source()
