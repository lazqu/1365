# 1365 자원봉사 공공 API 참고 문서 (API Specification)

> [!NOTE]
> 🚧 **참고용 초안 (Draft / 백업 문서)**
> 본 문서는 1365 봉사참여정보서비스 공공 API 명세 및 XML 칼럼 정보를 참고용으로 보관해둔 백업 문서입니다.

---

## 📋 1. 1365 Open API 개요

- **공공 데이터 포털 서비스명**: 행정안전부 봉사참여정보서비스
- **Base URL**: `http://apis.data.go.kr/1741000/volunteerPartcptnService`
- **주요 오퍼레이션**:
  - `getVltrSearchWordList`: 봉사참여정보 목록 조회 (요약/목록 API)
  - `getVltrPartcptnItem`: 봉사참여정보 상세 정보 조회 (상세 API)

---

## 📑 2. XML 주요 칼럼(태그) 명세표

| 영문 칼럼명 | 한글 명칭 | 설명 및 반환 형태 예시 |
| :--- | :--- | :--- |
| `progrmRegistNo` | **프로그램 등록번호** | 봉사활동 고유 식별 ID |
| `progrmSj` | **봉사 제목** | 봉사활동 프로그램 제목 |
| `progrmSttusSe` | **모집 상태 코드** | `1`: 모집전, `2`: 모집중, `3`: 모집마감 |
| `progrmBgnde` | **봉사 시작일** | YYYYMMDD |
| `progrmEndde` | **봉사 종료일** | YYYYMMDD |
| `noticeBgnde` | **모집 시작일** | YYYYMMDD |
| `noticeEndde` | **모집 종료일** | YYYYMMDD |
| `actBeginTm` | **활동 시작 시간** | 시 단위 |
| `actEndTm` | **활동 종료 시간** | 시 단위 |
| `actPlace` | **봉사 장소** | 봉사 활동 장소 명칭 |
| `actWkdy` | **활동 요일** | 월~일 비트열 (예: `0010000`) |
| `rcritNmpr` | **모집 정원** | 총 모집 인원수 |
| `appTotal` | **신청 인원** | 현재 신청 인원수 |
| `adultPosblAt` | **성인 가능 여부** | `Y` / `N` |
| `yngbgsPosblAt` | **청소년 가능 여부** | `Y` / `N` |
| `familyPosblAt` | **가족 가능 여부** | `Y` / `N` |
| `grpPosblAt` | **단체 가능 여부** | `Y` / `N` |
| `pbsvntPosblAt` | **공무원 가능 여부** | `Y` / `N` |
| `nanmmbyNm` | **나눔주체 명칭** | 봉사 모집 기관 / 단체명 |
| `nanmmbyNmAdmn` | **담당자 이름** | 모집 담당자 성명 |
| `mnnstNm` | **주관 기관명** | 주관 행정기관명 |
| `sidoCd` | **시도 코드** | 행정구역 시도 코드 |
| `gugunCd` | **시군구 코드** | 행정구역 시군구 코드 |
| `srvcClCode` | **봉사 분야** | 서비스 분류 |
| `postAdres` | **우편 주소** | 상세 봉사 장소 주소 |
| `telno` | **전화번호** | 담당자 / 센터 연락처 |
| `email` | **이메일** | 담당자 이메일 주소 |
| `progrmCn` | **봉사 상세 내용** | 봉사활동 상세 모집요강 및 준비물 |

---

## 💻 3. 언어별 API 호출 예제 (Code Samples)

### Python (파이썬 XML 호출 예시)
```python
import urllib.request
import xml.etree.ElementTree as ET

service_key = "YOUR_SERVICE_KEY"
url = f"http://apis.data.go.kr/1741000/volunteerPartcptnService/getVltrSearchWordList?serviceKey={service_key}&numOfRows=10&pageNo=1"

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req) as response:
    xml_data = response.read().decode('utf-8')
    root = ET.fromstring(xml_data)
    
    for item in root.findall('.//item'):
        progrm_id = item.findtext('progrmRegistNo')
        title = item.findtext('progrmSj')
        org = item.findtext('nanmmbyNm')
        print(f"[{progrm_id}] {title} ({org})")
```

### cURL
```bash
curl -X GET "http://apis.data.go.kr/1741000/volunteerPartcptnService/getVltrSearchWordList?serviceKey=YOUR_SERVICE_KEY&numOfRows=10&pageNo=1"
```
