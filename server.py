#!/usr/bin/env python3
"""
小松工作台 - 本地服务器
功能：静态文件服务 + 油价API代理（支持豆包大模型联网搜索）
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import re
import os
import sys
from datetime import datetime

PORT = 8090
WEB_DIR = os.path.dirname(os.path.abspath(__file__))

# 豆包大模型配置
DOUBAO_API_URL = 'https://ark.cn-beijing.volces.com/api/v3/responses'
DOUBAO_MODEL = 'doubao-seed-2-1-pro-260628'

# 省份名称 -> 57148.com URL 拼音映射
PROVINCE_MAP = {
    '湖南': 'hunan', '湖北': 'hubei', '广东': 'guangdong', '广西': 'guangxi',
    '北京': 'beijing', '天津': 'tianjin', '上海': 'shanghai', '重庆': 'chongqing',
    '四川': 'sichuan', '贵州': 'guizhou', '云南': 'yunnan', '西藏': 'xizang',
    '陕西': 'shanxi3', '甘肃': 'gansu', '青海': 'qinghai', '宁夏': 'ningxia',
    '新疆': 'xinjiang', '河南': 'henan', '河北': 'hebei', '山西': 'shanxi',
    '山东': 'shandong', '安徽': 'anhui', '浙江': 'zhejiang', '江苏': 'jiangsu',
    '福建': 'fujian', '江西': 'jiangxi', '海南': 'hainan', '吉林': 'jilin',
    '黑龙江': 'heilongjiang', '辽宁': 'liaoning', '内蒙古': 'neimenggu',
}

# 金投网 regionId 映射 cngold.org datacenter API
CNGOLD_REGION_MAP = {
    '北京': 2, '上海': 4, '天津': 3, '重庆': 5,
    '河北': 6, '石家庄': 6, '山西': 7, '太原': 7,
    '辽宁': 8, '沈阳': 8, '吉林': 9, '长春': 9,
    '黑龙江': 10, '哈尔滨': 10, '江苏': 11, '南京': 11, '苏州': 11,
    '浙江': 12, '杭州': 12, '宁波': 12, '安徽': 13, '合肥': 13,
    '福建': 14, '福州': 14, '厦门': 14, '江西': 15, '南昌': 15,
    '山东': 16, '济南': 16, '青岛': 16, '河南': 17, '郑州': 17,
    '湖北': 18, '武汉': 18, '湖南': 19, '长沙': 19, '株洲': 19, '湘潭': 19,
    '广东': 20, '广州': 20, '深圳': 20, '东莞': 20, '海南': 21, '海口': 21,
    '四川': 22, '成都': 22, '贵州': 23, '贵阳': 23, '云南': 24, '昆明': 24,
    '陕西': 25, '西安': 25, '甘肃': 26, '兰州': 26,
    '内蒙古': 28, '呼和浩特': 28, '宁夏': 29, '银川': 29,
    '新疆': 30, '乌鲁木齐': 30, '广西': 31, '南宁': 31,
    '青海': 27, '西宁': 27, '西藏': 32, '拉萨': 32,
}

# 省份名简称映射（用户可能输入"长沙"但需要查"湖南"）
CITY_TO_PROVINCE = {
    '长沙': '湖南', '株洲': '湖南', '湘潭': '湖南', '衡阳': '湖南',
    '武汉': '湖北', '广州': '广东', '深圳': '广东',
    '杭州': '浙江', '宁波': '浙江', '南京': '江苏', '苏州': '江苏',
    '成都': '四川', '西安': '陕西', '郑州': '河南', '济南': '山东',
    '合肥': '安徽', '福州': '福建', '南昌': '江西', '昆明': '云南',
    '贵阳': '贵州', '兰州': '甘肃', '海口': '海南', '太原': '山西',
    '沈阳': '辽宁', '长春': '吉林', '哈尔滨': '黑龙江',
    '石家庄': '河北', '呼和浩特': '内蒙古', '乌鲁木齐': '新疆',
    '银川': '宁夏', '西宁': '青海', '拉萨': '西藏', '南宁': '广西',
    '北京': '北京', '上海': '上海', '天津': '天津', '重庆': '重庆',
}


def normalize_province(province):
    """将城市名转换为省份名"""
    for city, prov in CITY_TO_PROVINCE.items():
        if city in province:
            return prov
    return province


def fetch_oil_price_doubao(api_key, province):
    """使用豆包大模型联网搜索获取最新油价"""
    province = normalize_province(province)

    prompt = (
        f'请搜索{province}今日最新油价（{datetime.now().strftime("%Y年%m月%d日")}），'
        f'返回92号汽油、95号汽油、98号汽油、0号柴油的零售价格（元/升）。'
        f'请只返回JSON格式，不要其他文字：'
        f'{{"p92":"7.73","p95":"8.22","p98":"9.42","p0":"7.52"}}'
    )

    payload = {
        'model': DOUBAO_MODEL,
        'tools': [
            {
                'type': 'web_search',
                'max_keyword': 3,
            }
        ],
        'input': [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'input_text',
                        'text': prompt,
                    }
                ]
            }
        ],
    }

    try:
        req = urllib.request.Request(
            DOUBAO_API_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
            },
            method='POST',
        )
        resp = urllib.request.urlopen(req, timeout=30)
        raw = resp.read().decode('utf-8', errors='replace')
        data = json.loads(raw)

        # 从返回结果中提取文本
        text = ''
        if 'output' in data:
            for item in data['output']:
                if item.get('type') == 'message' and item.get('role') == 'assistant':
                    for content in item.get('content', []):
                        text += content.get('text', '')
        elif 'output_text' in data:
            text = data['output_text']
        else:
            # 尝试其他格式
            text = json.dumps(data, ensure_ascii=False)

        # 从文本中提取 JSON 格式的油价
        prices = parse_oil_prices_from_text(text)

        if prices and len(prices) >= 3:
            prices.setdefault('p0', '')
            return {
                'prices': prices,
                'province': province,
                'source': '豆包大模型(联网搜索)',
                'fetchedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': None,
                'raw_text': text[:500],
            }

        return {
            'error': '豆包返回数据解析失败',
            'prices': None,
            'province': province,
            'raw_text': text[:500],
        }

    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8', errors='replace')
        return {
            'error': f'豆包API错误({e.code}): {err_body[:200]}',
            'prices': None,
            'province': province,
        }
    except Exception as e:
        return {
            'error': f'豆包API请求失败: {str(e)}',
            'prices': None,
            'province': province,
        }


def parse_oil_prices_from_text(text):
    """从豆包返回的文本中提取油价数据"""
    prices = {}

    # 方法1: 尝试提取 JSON
    json_match = re.search(r'\{[^}]*"p92"[^}]*\}', text)
    if json_match:
        try:
            j = json.loads(json_match.group())
            for k in ['p92', 'p95', 'p98', 'p0']:
                if k in j:
                    prices[k] = str(j[k]).replace('元', '').replace('/升', '').strip()
        except (json.JSONDecodeError, KeyError):
            pass

    if len(prices) >= 3:
        return prices

    # 方法2: 正则匹配 "92号汽油" + 价格
    patterns = [
        (r'92号汽油[^\d]*([\d.]+)', 'p92'),
        (r'95号汽油[^\d]*([\d.]+)', 'p95'),
        (r'98号汽油[^\d]*([\d.]+)', 'p98'),
        (r'0号柴油[^\d]*([\d.]+)', 'p0'),
    ]
    for pattern, key in patterns:
        m = re.search(pattern, text)
        if m:
            prices[key] = m.group(1)

    if len(prices) >= 3:
        return prices

    # 方法3: 匹配 "92#" + 价格
    patterns2 = [
        (r'92#[^\d]*([\d.]+)', 'p92'),
        (r'95#[^\d]*([\d.]+)', 'p95'),
        (r'98#[^\d]*([\d.]+)', 'p98'),
        (r'0#[^\d]*([\d.]+)', 'p0'),
    ]
    for pattern, key in patterns2:
        m = re.search(pattern, text)
        if m:
            prices[key] = m.group(1)

    return prices


def fetch_oil_price_cngold(province):
    """从金投网 datacenter API 获取油价数据（JSON接口，更新最及时）"""
    province = normalize_province(province)

    region_id = CNGOLD_REGION_MAP.get(province)
    if not region_id:
        # 尝试模糊匹配
        for prov_name, rid in CNGOLD_REGION_MAP.items():
            if province in prov_name or prov_name in province:
                region_id = rid
                break

    if not region_id:
        return None

    url = f'https://datacenter.cngold.org/city_oil/price_history/?regionId={region_id}'

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
            'Referer': 'https://m.cngold.org/quote/oil/youjia_c312.html',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
        })
        resp = urllib.request.urlopen(req, timeout=10)
        raw = resp.read().decode('utf-8', errors='replace')
        data = json.loads(raw)

        if data.get('returnCode') == 0 and data.get('data'):
            latest = data['data'][0]  # 第一条是最新数据
            prices = {
                'p92': str(latest.get('n92', '')),
                'p95': str(latest.get('n95', '')),
                'p98': str(latest.get('n98', '')),
                'p0': str(latest.get('n0', '')),
            }

            # 过滤无效值
            valid = {k: v for k, v in prices.items() if v and float(v) > 0}
            if len(valid) >= 3:
                prices.setdefault('p0', '')
                return {
                    'prices': prices,
                    'province': province,
                    'source': '金投网(cngold.org)',
                    'fetchedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'error': None,
                    'date': latest.get('date', ''),
                }

        return None

    except Exception:
        return None


def fetch_oil_price_57148(province):
    """从 57148.com 抓取油价数据（备用）"""
    province = normalize_province(province)

    pinyin = PROVINCE_MAP.get(province)
    if not pinyin:
        for prov_name, py in PROVINCE_MAP.items():
            if province in prov_name or prov_name in province:
                pinyin = py
                province = prov_name
                break

    if not pinyin:
        return None

    url = f'https://m.57148.com/{pinyin}.html'

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36'
        })
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode('utf-8', errors='replace')
        text = re.sub(r'<[^>]+>', '', html)

        # 方法1: 文本格式
        m = re.search(
            r'92号汽油为([\d.]+)元.*?95号汽油为([\d.]+)元.*?98号汽油为([\d.]+)元.*?0号柴油为([\d.]+)元',
            text
        )
        if m:
            return {
                'prices': {'p92': m.group(1), 'p95': m.group(2), 'p98': m.group(3), 'p0': m.group(4)},
                'province': province,
                'source': '57148.com',
                'fetchedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': None,
            }

        # 方法2: 表格 TD 格式
        tds = re.findall(r'<td[^>]*>\s*([789]\.\d{2})\s*</td>', html)
        if len(tds) >= 4:
            return {
                'prices': {'p92': tds[0], 'p95': tds[1], 'p98': tds[2], 'p0': tds[3]},
                'province': province,
                'source': '57148.com',
                'fetchedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': None,
            }

        # 方法3: 模糊搜索
        prices = {}
        for oil_type, key in [('92', 'p92'), ('95', 'p95'), ('98', 'p98')]:
            m2 = re.search(rf'{oil_type}#汽油.*?([\d.]+)', text)
            if m2:
                prices[key] = m2.group(1)
        m3 = re.search(r'0#柴油.*?([\d.]+)', text)
        if m3:
            prices['p0'] = m3.group(1)
        if len(prices) >= 3:
            prices.setdefault('p0', '')
            return {
                'prices': prices,
                'province': province,
                'source': '57148.com',
                'fetchedAt': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'error': None,
            }

        return None

    except Exception:
        return None


def fetch_oil_price(province, doubao_api_key=None):
    """
    获取油价 - 优先级：豆包大模型 > 金投网 > 57148.com
    """
    province = normalize_province(province)

    # 1. 优先使用豆包大模型（如果提供了API Key）
    if doubao_api_key:
        result = fetch_oil_price_doubao(doubao_api_key, province)
        if result and result.get('prices'):
            return result
        # 豆包失败，继续尝试其他数据源

    # 2. 金投网（更新更及时）
    result = fetch_oil_price_cngold(province)
    if result and result.get('prices'):
        return result

    # 3. 57148.com（备用）
    result = fetch_oil_price_57148(province)
    if result and result.get('prices'):
        return result

    # 全部失败
    return {
        'error': f'所有数据源均获取失败: {province}',
        'prices': None,
        'province': province,
    }


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        # API 路由
        if self.path.startswith('/api/oilprice'):
            self.handle_oil_price_api()
            return

        # 静态文件
        super().do_GET()

    def handle_oil_price_api(self):
        # Python http.server 默认用 Latin-1 解码 URL，需要修复中文编码
        raw_path = self.path
        parsed = urllib.parse.urlparse(raw_path)
        params = urllib.parse.parse_qs(parsed.query)
        province = params.get('prov', ['湖南'])[0]
        doubao_key = params.get('doubao_key', [None])[0]

        # 修复编码
        try:
            province = province.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass

        sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] 油价查询: prov={province}, doubao={'yes' if doubao_key else 'no'}\n")

        result = fetch_oil_price(province, doubao_api_key=doubao_key)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        msg = format % args
        if 'api/oilprice' in msg:
            sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        elif '404' not in msg:
            sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")


def main():
    for port in [PORT, 8091, 8092, 8093]:
        try:
            with socketserver.TCPServer(("", port), CustomHandler) as httpd:
                print(f"🚀 小松工作台服务器已启动: http://localhost:{port}/")
                print(f"📍 油价API: http://localhost:{port}/api/oilprice?prov=湖南")
                print(f"🤖 豆包API: http://localhost:{port}/api/oilprice?prov=湖南&doubao_key=YOUR_KEY")
                print(f"按 Ctrl+C 停止")
                httpd.serve_forever()
                break
        except OSError:
            continue


if __name__ == '__main__':
    main()
