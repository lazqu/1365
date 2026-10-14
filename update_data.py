import os
import re
import sys
import json
import time
import urllib.error
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

BASE_URL = "https://apis.data.go.kr/1741000/volunteerPartcptnService"
MAX_ATTEMPTS = 3
# XML 1.0 permits tab, LF, CR, U+0020–D7FF, U+E000–FFFD and
# U+10000–10FFFF. Replace only characters outside these ranges.
INVALID_XML_CHARS = re.compile(
    r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]"
)


def save_response_diagnostics(raw_data, headers, status, error, page_no, attempt):
    """Keep the original response and bounded context without logging its URL/key."""
    directory = os.path.join(os.path.dirname(__file__), "diagnostics")
    os.makedirs(directory, exist_ok=True)
    name = f"{datetime.now(KST).strftime('%Y%m%d_%H%M%S_%f')}_page{page_no}_attempt{attempt}"
    base = os.path.join(directory, name)
    with open(base + ".bin", "wb") as f:
        f.write(raw_data)
    details = {"page": page_no, "attempt": attempt, "status": status,
               "headers": headers, "byteLength": len(raw_data), "error": str(error)}
    if isinstance(error, ET.ParseError):
        line, column = error.position
        # Match ElementTree's line counting, including CR/CRLF normalization.
        text = raw_data.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        lines = text.split("\n")
        context = lines[line - 1][max(0, column - 100):column + 100]
        details.update(line=line, column=column, contextRepr=repr(context),
                       contextUtf8Hex=context.encode("utf-8").hex(" "))
    elif isinstance(error, UnicodeDecodeError):
        details.update(byteOffset=error.start,
                       contextHex=raw_data[max(0, error.start - 50):error.end + 50].hex(" "))
    with open(base + ".json", "w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=2)
    print(f"[WARN] 원본 응답 및 진단 정보 저장: {base}.bin / .json", file=sys.stderr)

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
        raise RuntimeError("SERVICE_KEY가 설정되지 않았습니다.")

    params = {
        "serviceKey": SERVICE_KEY,
        "op": "getVltrSearchWordList",
        "numOfRows": str(page_size),
        "pageNo": str(page_no)
    }
    query_string = urllib.parse.urlencode(params)
    url = f"{BASE_URL}/getVltrSearchWordList?{query_string}"

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"[{datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')}] API 수집 요청 (page {page_no}, 시도 {attempt}/{MAX_ATTEMPTS})...")
        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                raw_data = response.read()
                response_headers = dict(response.headers.items()) if hasattr(response, "headers") else {}
                response_status = getattr(response, "status", None)
            try:
                xml_data = raw_data.decode("utf-8")
                xml_data, control_count = INVALID_XML_CHARS.subn(" ", xml_data)
                if control_count:
                    print(
                        f"[WARN] page {page_no}: XML 금지 문자 {control_count}개를 스페이스(U+0020)로 치환했습니다.",
                        file=sys.stderr,
                    )
                root = ET.fromstring(xml_data)
            except (ET.ParseError, UnicodeDecodeError) as e:
                save_response_diagnostics(
                    raw_data, response_headers, response_status, e, page_no, attempt
                )
                raise

            header = root.find("header")
            if header is None:
                raise RuntimeError("API 응답에 header가 없습니다.")
            code = header.findtext("resultCode")
            msg = header.findtext("resultMsg")
            if code != "00":
                raise RuntimeError(f"API Error {code}: {msg}")

            body = root.find("body")
            if body is None:
                raise RuntimeError("API 응답에 body가 없습니다.")
            total_count_str = body.findtext("totalCount")
            items_node = body.find("items")
            if total_count_str is None or items_node is None:
                raise RuntimeError("API 응답에서 totalCount 또는 items를 찾을 수 없습니다.")

            total_count = int(total_count_str)
            if total_count < 0:
                raise ValueError("API totalCount는 음수일 수 없습니다.")
            items = [xml_to_dict(item_node) for item_node in items_node.findall("item")]
            return items, total_count
        except (RuntimeError, ValueError) as e:
            # API error codes, missing fields and invalid totalCount are not
            # transient: preserve the response and keep the original failure.
            save_response_diagnostics(
                raw_data, response_headers, response_status, e, page_no, attempt
            )
            raise
        except urllib.error.HTTPError as e:
            with e:
                save_response_diagnostics(
                    e.read(), dict(e.headers.items()) if e.headers else {}, e.code,
                    RuntimeError(f"API HTTP Error {e.code}: {e.reason}"), page_no, attempt,
                )
            if e.code != 429 and not 500 <= e.code < 600:
                raise RuntimeError(f"API HTTP Error {e.code}: {e.reason}") from e
            error = e
        except (urllib.error.URLError, OSError, ET.ParseError, UnicodeDecodeError) as e:
            error = e

        if attempt == MAX_ATTEMPTS:
            raise RuntimeError(f"페이지 {page_no} 수집 실패 ({MAX_ATTEMPTS}회 시도): {error}") from error

        delay = 2 ** (attempt - 1)
        print(f"[WARN] API 응답 수집/파싱 오류: {error}. {delay}초 후 재시도합니다.", file=sys.stderr)
        time.sleep(delay)

def run_update():
    print("=== 1365 자원봉사 데이터 자동 수집 시작 ===")
    all_items = []
    page_no = 1
    page_size = 10000
    total_count = 0

    while True:
        items, count = fetch_page(page_no=page_no, page_size=page_size)
        if page_no == 1:
            total_count = count

        if items:
            all_items.extend(items)

        if len(all_items) >= total_count:
            break
        if len(items) < page_size:
            raise RuntimeError(
                f"수집이 완료되지 않았습니다: API 전체 {total_count}건 중 {len(all_items)}건 수집"
            )
        page_no += 1

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
