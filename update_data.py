import os
import sys
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

BASE_URL = "https://apis.data.go.kr/1741000/volunteerPartcptnService"

def load_env():
    """.env 파일에서 환경변수 로드"""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip().strip("'\""))

load_env()
SERVICE_KEY = os.environ.get("SERVICE_KEY")

def xml_to_dict(element):
    """ElementTree 객체를 딕셔너리로 변환"""
    result = {}
    for child in element:
        if len(child) == 0:
            result[child.tag] = child.text
        else:
            result[child.tag] = xml_to_dict(child)
    return result

def fetch_page(page_no=1, page_size=10000):
    if not SERVICE_KEY:
        print("[ERROR] SERVICE_KEY가 설정되지 않았습니다.", file=sys.stderr)
        return None, 0

    params = {
        "serviceKey": SERVICE_KEY,
        "op": "getVltrSearchWordList",
        "numOfRows": str(page_size),
        "pageNo": str(page_no)
    }
    query_string = urllib.parse.urlencode(params)
    url = f"{BASE_URL}/getVltrSearchWordList?{query_string}"

    print(f"[{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}] API 수집 요청 (page {page_no})...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            xml_data = response.read().decode("utf-8")
            root = ET.fromstring(xml_data)
            
            header = root.find("header")
            if header is not None:
                code = header.findtext("resultCode")
                msg = header.findtext("resultMsg")
                if code != "00":
                    print(f"[API Error {code}] {msg}", file=sys.stderr)
                    return [], 0

            total_count_str = root.findtext(".//body/totalCount") or "0"
            total_count = int(total_count_str)

            items_node = root.find(".//items")
            items = []
            if items_node is not None:
                for item_node in items_node.findall("item"):
                    items.append(xml_to_dict(item_node))
            
            return items, total_count
    except Exception as e:
        print(f"[Error] 수집 중 예외 발생: {e}", file=sys.stderr)
        return [], 0

def run_update():
    print("=== 1365 자원봉사 데이터 자동 수집 시작 ===")
    all_items = []
    page_no = 1
    page_size = 10000
    total_count = 0

    while True:
        items, count = fetch_page(page_no=page_no, page_size=page_size)
        if page_no == 1:
            total_count = count or len(items)

        if items:
            all_items.extend(items)

        if len(items) == page_size and len(all_items) < total_count:
            page_no += 1
        else:
            break

    # 중복 제거 (progrmRegistNo 기준)
    unique_map = {}
    for item in all_items:
        reg_no = item.get("progrmRegistNo")
        if reg_no and reg_no not in unique_map:
            unique_map[reg_no] = item
    
    final_items = list(unique_map.values())
    now_str = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")

    output_data = {
        "updatedAt": now_str,
        "totalCount": len(final_items),
        "items": final_items
    }

    out_path = os.path.join(os.path.dirname(__file__), "data.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    js_path = os.path.join(os.path.dirname(__file__), "data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("window.STATIC_1365_DATA = ")
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        f.write(";\n")

    print(f"[SUCCESS] Total {len(final_items)} items collected -> {out_path} and {js_path} ({now_str})")

if __name__ == "__main__":
    run_update()
