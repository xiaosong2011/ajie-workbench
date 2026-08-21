#!/usr/bin/env python3
"""
抓取全国各省油价数据，生成 oil-data.json
数据来源: qiyoujiage.com
"""
import json
import re
import urllib.request
import ssl
import os
from datetime import datetime

# 城市配置 (slug -> 显示名称)
CITIES = {
    "hunan": "长沙(湖南)",
    "beijing": "北京",
    "shanghai": "上海",
    "guangdong": "广州(广东)",
    "shenzhen": "深圳",
    "hubei": "武汉(湖北)",
    "sichuan": "成都(四川)",
    "zhejiang": "杭州(浙江)",
    "jiangsu": "南京(江苏)",
    "henan": "郑州(河南)",
    "shandong": "济南(山东)",
    "hebei": "石家庄(河北)",
    "fujian": "福州(福建)",
    "jiangxi": "南昌(江西)",
    "guangxi": "南宁(广西)",
    "yunnan": "昆明(云南)",
    "guizhou": "贵阳(贵州)",
    "anhui": "合肥(安徽)",
    "shanxi": "太原(山西)",
    "shanxi-3": "西安(陕西)",
    "heilongjiang": "哈尔滨(黑龙江)",
    "jilin": "长春(吉林)",
    "liaoning": "沈阳(辽宁)",
    "hainan": "海口(海南)",
    "gansu": "兰州(甘肃)",
    "qinghai": "西宁(青海)",
    "xinjiang": "乌鲁木齐(新疆)",
    "xizang": "拉萨(西藏)",
    "ningxia": "银川(宁夏)",
    "neimenggu": "呼和浩特(内蒙古)",
    "chongqing": "重庆",
    "tianjin": "天津",
}

def fetch_page(slug):
    """获取油价页面HTML"""
    url = f"http://www.qiyoujiage.com/{slug}.shtml"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        return resp.read().decode("utf-8", errors="replace")

def parse_prices(html):
    """解析油价HTML，返回价格列表"""
    prices = []
    # 匹配 <dt>XX92#汽油</dt> 和 <dd>7.73</dd>
    dt_pattern = r'<dt>[^<]*?(\d{1,2})#?(汽油|柴油)[^<]*</dt>'
    dd_pattern = r'<dd[^>]*>([\d.]+)'
    
    dt_matches = re.findall(dt_pattern, html, re.IGNORECASE)
    dd_matches = re.findall(dd_pattern, html, re.IGNORECASE)
    
    for i in range(min(len(dt_matches), len(dd_matches))):
        num, fuel_type = dt_matches[i]
        price = dd_matches[i]
        name = "0号柴油" if fuel_type == "柴油" else f"{num}号汽油"
        prices.append({"name": name, "price": price})
    
    return prices

def extract_date(html):
    """提取更新日期"""
    m = re.search(r'(\d{4}[-年]\d{1,2}[-月]\d{1,2})', html)
    return m.group(1) if m else ""

def extract_next_adjust(html):
    """提取下次调价信息"""
    m = re.search(r'下次油价[^，。<]*调整', html)
    return m.group(0) if m else ""

def main():
    result = {
        "updatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cities": {}
    }
    
    for slug, display_name in CITIES.items():
        try:
            html = fetch_page(slug)
            prices = parse_prices(html)
            date_str = extract_date(html)
            next_adjust = extract_next_adjust(html)
            
            if prices:
                result["cities"][slug] = {
                    "name": display_name,
                    "prices": prices,
                    "date": date_str,
                    "nextAdjust": next_adjust
                }
                print(f"✅ {display_name}: {len(prices)} prices fetched")
            else:
                print(f"⚠️  {display_name}: no prices parsed")
        except Exception as e:
            print(f"❌ {display_name}: {e}")
            result["cities"][slug] = {
                "name": display_name,
                "prices": [],
                "date": "",
                "nextAdjust": "",
                "error": str(e)
            }
    
    # 写入 JSON 文件
    output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "oil-data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📦 oil-data.json saved to {output_path}")
    print(f"📊 Total cities: {len(result['cities'])}")

if __name__ == "__main__":
    main()
