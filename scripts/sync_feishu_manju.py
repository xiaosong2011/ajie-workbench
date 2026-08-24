#!/usr/bin/env python3
"""
飞书多维表格数据同步脚本
从飞书多维表格拉取漫剧数据，保存为 JSON 文件供前端直接读取
"""

import json
import os
import sys
import urllib.request
import urllib.error
import time

def get_tenant_access_token(app_id, app_secret):
    """获取飞书应用 tenant_access_token"""
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({
        "app_id": app_id,
        "app_secret": app_secret
    }).encode("utf-8")
    
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json"
    })
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            if result.get("code") == 0:
                return result["tenant_access_token"]
            else:
                print(f"❌ 获取Token失败: {result.get('msg')}")
                return None
    except Exception as e:
        print(f"❌ 获取Token异常: {e}")
        return None

def fetch_bitable_records(token, app_token, table_id, page_size=100):
    """从多维表格获取所有记录"""
    all_items = []
    page_token = None
    
    while True:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records?page_size={page_size}"
        if page_token:
            url += f"&page_token={page_token}"
        
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {token}"
        })
        
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                if result.get("code") != 0:
                    print(f"❌ 获取记录失败: {result.get('msg')}")
                    return None
                
                data = result.get("data", {})
                items = data.get("items", [])
                all_items.extend(items)
                
                if data.get("has_more") and data.get("page_token"):
                    page_token = data["page_token"]
                else:
                    break
        except Exception as e:
            print(f"❌ 获取记录异常: {e}")
            return None
    
    return all_items

def transform_records(items):
    """转换记录格式为前端可用格式"""
    result = []
    for item in items:
        fields = item.get("fields", {})
        # 跳过空记录
        if not fields or not any(fields.values()):
            continue
        result.append({
            "recordId": item.get("record_id", ""),
            "title": fields.get("漫剧别名", "") or fields.get("名称", "") or "未命名",
            "bookId": fields.get("书名ID", "") or "",
            "fields": fields
        })
    return result

def main():
    # 从环境变量读取配置
    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    base_token = os.environ.get("FEISHU_BASE_TOKEN", "")
    table_id = os.environ.get("FEISHU_TABLE_ID", "")
    output_file = os.environ.get("OUTPUT_FILE", "feishu-manju.json")
    
    if not app_id or not app_secret or not base_token or not table_id:
        print("❌ 缺少必要的环境变量: FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_BASE_TOKEN, FEISHU_TABLE_ID")
        sys.exit(1)
    
    print("🚀 开始同步飞书漫剧数据...")
    print(f"   Base: {base_token}")
    print(f"   表: {table_id}")
    
    # 1. 获取 token
    print("\n1️⃣  获取 access_token...")
    token = get_tenant_access_token(app_id, app_secret)
    if not token:
        sys.exit(1)
    print(f"   ✅ Token获取成功: {token[:15]}...")
    
    # 2. 获取记录
    print("\n2️⃣  获取多维表格记录...")
    items = fetch_bitable_records(token, base_token, table_id)
    if items is None:
        sys.exit(1)
    print(f"   ✅ 获取到 {len(items)} 条记录")
    
    # 3. 转换格式
    print("\n3️⃣  转换数据格式...")
    data_list = transform_records(items)
    print(f"   ✅ 有效记录 {len(data_list)} 条（已跳过空记录）")
    
    # 4. 保存到文件
    print(f"\n4️⃣  保存到 {output_file}...")
    output = {
        "data": data_list,
        "total": len(data_list),
        "updateTime": int(time.time() * 1000),
        "updateTimeStr": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ 保存成功！")
    print(f"\n🎉 同步完成！共 {len(data_list)} 条漫剧数据")

if __name__ == "__main__":
    main()
