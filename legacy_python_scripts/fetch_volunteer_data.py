import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import os
import sys

BASE_URL = "http://apis.data.go.kr/1741000/volunteerPartcptnService"

def load_env():
    """Load variables from .env file if present"""
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
if not SERVICE_KEY:
    print("[ERROR] SERVICE_KEY is not set in .env file or environment variables!", file=sys.stderr)
    sys.exit(1)

def fetch_data(operation="getVltrSearchWordList", params=None):
    """
    1365 봉사참여정보 API 데이터 조회
    
    오퍼레이션 목록:
    1. getVltrSearchWordList (검색어/키워드별 봉사정보 목록)
    2. getVltrAreaList (지역별 봉사정보 목록)
    3. getVltrCategoryList (분야별 봉사정보 목록)
    4. getVltrPeriodStatList (기간별 통계/목록)
    5. getVltrPartcptnItem (상세정보 조회, progrmRegistNo 필요)
    """
    if params is None:
        params = {}
    
    key = params.get("serviceKey") or SERVICE_KEY
    if not key:
        print("Error: SERVICE_KEY가 설정되지 않았습니다. .env 파일이나 환경 변수(SERVICE_KEY)를 설정해주세요.")
        return None
    
    params["serviceKey"] = key
    if "numOfRows" not in params:
        params["numOfRows"] = "10"
    if "pageNo" not in params:
        params["pageNo"] = "1"
        
    query_string = urllib.parse.urlencode(params)
    url = f"{BASE_URL}/{operation}?{query_string}"
    
    print(f"Requesting: {url}\n")
    
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read().decode("utf-8")
            return xml_data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def xml_to_dict(element):
    """Simple XML to dict converter"""
    result = {}
    for child in element:
        if len(child) == 0:
            result[child.tag] = child.text
        else:
            result[child.tag] = xml_to_dict(child)
    return result

def parse_items(xml_str):
    if not xml_str:
        return []
    
    root = ET.fromstring(xml_str)
    header = root.find("header")
    if header is not None:
        code = header.findtext("resultCode")
        msg = header.findtext("resultMsg")
        if code != "00":
            print(f"API Error [{code}]: {msg}")
            return []
            
    items_node = root.find(".//items")
    if items_node is None:
        return []
        
    items = []
    for item_node in items_node.findall("item"):
        items.append(xml_to_dict(item_node))
    return items

if __name__ == "__main__":
    op = sys.argv[1] if len(sys.argv) > 1 else "getVltrSearchWordList"
    
    print(f"=== 1365 자원봉사 참여정보 조회 [{op}] ===")
    xml_res = fetch_data(op, {"numOfRows": "5", "pageNo": "1"})
    
    if xml_res:
        parsed = parse_items(xml_res)
        print(f"조회된 항목 수: {len(parsed)}")
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
