# 1365 자원봉사 스마트 탐색기 & OpenAPI 가이드

행정안전부 **봉사참여정보서비스 (1365 자원봉사 포털)** 오픈 API 연동 문서, 웹 탐색기 대시보드 및 파이썬 데이터 분석 모듈입니다.

---

## 📌 1. 프로젝트 개요 (Overview)

본 프로젝트는 1365 자원봉사 공공 API의 부실한 검색 기능과 느린 네트워크 대기시간을 극복하기 위해 개발되었습니다. 

* **핵심 아키텍처 (2단계 파이프라인 ⚡)**:
  1. **[1단계 수집]**: API 통신 1회로 원천 데이터를 일괄 수집
  2. **[2단계 필터링]**: 추가 네트워크 요청 **0회**, 브라우저/메모리 상에서 **0.001초 만에 즉시 반응형 필터링 및 다중 정렬**
* **이중 플랫폼 지원**:
  - 💻 **반응형 웹 대시보드 Explorer (`index.html`)**: 설치 없이 웹 브라우저에서 시각적으로 탐색
  - 🐍 **파이썬 데이터 분석 모듈 (`volunteer_search.py`, `area_mapper.py`)**: Jupyter Notebook 및 자동화 스크립트용

---

## 🚀 2. 빠른 시작 가이드 (Quick Start)

### 1단계: 보안 환경변수 (`.env`) 설정
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 공공데이터포털에서 발급받은 `SERVICE_KEY`를 설정합니다.
```env
SERVICE_KEY=your_actual_service_key_here
```
> 🔒 `.env` 파일은 `.gitignore`에 등록되어 있어 Git 저장소로 인증키가 노출되지 않습니다.

### 2단계: 백엔드 프록시 서버 실행
클라이언트 자바스크립트에서 인증키가 노출되는 것을 방지하기 위해 로컬 프록시 서버를 실행합니다.
```bash
python server.py
```

### 3단계: 웹 대시보드 접속
웹 브라우저를 열고 아래 주소로 접속합니다.
```text
http://localhost:3000
```

---

## ✨ 3. 주요 기능 및 아키텍처 상세 (Core Features)

### 💻 웹 대시보드 UI/UX (`index.html` & `area_mapper.js`)

1. **🖥️ 좌우 독립 분할 대시보드 레이아웃 (Slack / Notion 스타일)**:
   - **뷰포트 고정(100vh) 분할 구조**: 오른쪽 공고 목록을 스크롤해도 왼쪽 사이드바가 위로 사라지지 않고 항상 제자리 유지
   - **우측 3단 고정-스크롤 구조**: 상단 탭/건수 정보 및 하단 페이지네이션 바는 고정, 중앙 카드 목록 영역만 독립 스크롤
   - **슬림 커스텀 스크롤바**: 다크 테마에 맞춘 프리미엄 6px 반투명 스크롤바 적용
2. **🗺️ 전국 194개 지자체 커버 Area Mapper (`area_mapper.js`)**:
   - 대한민국 17개 시/도 및 194개 시/군/구의 복합키(`sidoCd_gugunCd`) 역매핑 100% 지원
   - 행정기관명 수거 및 자원봉사센터 정제 함수 (`cleanAgencyName`) 탑재
3. **🔀 노션(Notion) 스타일 동적 다중 정렬 블록 파이프라인**:
   - **전원 ON/OFF 스위치**: 정렬을 끄면 내가 맞춘 정렬 블록 설정은 그대로 보존(`🔒 원천 순서`)되면서 1365 포털 원천 수집 순서로 즉시 전환
   - **드래그 앤 드롭(`⠿`) & 원클릭 이동(`▲▼`)**: 정렬 블록의 위치를 자유롭게 끌어다 놓아 1차, 2차, 3차 우선순위 즉시 재배치
   - **동적 조건 추가/제거**: `+ 정렬 기준 추가` 및 `✕` 삭제 지원 (모집마감일, 모집시작일, 봉사시작일, 봉사종료일, 공고제목)
   - **독립적 정렬 방향 제어**: 각 블록별 독립적인 오름차순(⬆️)/내림차순(⬇️) 제어 및 0.001초 실시간 재정렬
4. **⚡ 0.001초 클라이언트 인메모리 페이징**:
   - API 통신 0회, 메모리 슬라이싱 방식의 `[◀ 이전] [1] [2] [3] [4] [5] [다음 ▶]` 0초 즉시 이동
   - 하단 고정 바에서 카드를 끝까지 내리지 않아도 언제든 즉시 다음/이전 페이지 이동 가능
   - 관심 등록(`★`) 및 숨기기(`🚫`) 버튼 클릭 시 **현재 보고 있는 페이지 위치 자동 보존**
5. **📅 한국어 요일 & 일일 봉사시간 자동 표기**:
   - 모든 날짜에 **한국어 요일 자동 계산** 표기 (예: `2026.09.01(화) ~ 2026.09.15(화)`)
   - 카드의 메타 정보에 **일일 활동시간** 표시 (예: `⏰ 시간: 9시 ~ 13시`)
6. **🔥 D-DAY 마감 임박 배지**:
   - `🔥 D-DAY (오늘마감)`, `⚠️ D-3`, `⏳ D-7`, `🚫 마감됨` 동적 태그 제공
7. **⭐ 관심 목록 & 🚫 개별 봉사 숨기기 (블랙리스트)**:
   - **`📋 전체 결과`** | **`⭐ 관심 목록`** | **`🚫 숨김 목록`** 3개 탭 제공
   - `localStorage` 기반 영구 지속성 (`1365_bookmarks`, `1365_hidden`, `1365_raw_cache`)

---

### 🐍 파이썬 수집 및 분석 모듈 (`volunteer_search.py`)

Pandas DataFrame 기반의 2단계 파이프라인으로 대용량 데이터를 고속 처리합니다.

```python
from volunteer_search import fetch_all_dataframe, filter_volunteers
from area_mapper import get_area_code, get_location_name

# [1단계] 원천 데이터 전체 수집 (네트워크 통신 1회)
df_all = fetch_all_dataframe(num_of_rows=1000)

# [2단계] 수집된 df_all로 다양한 조건 재검색 (네트워크 통신 0회, 0.001초 응답)
# 예시: 서울/경기 지역, 성인 가능 봉사, 모집마감일(오름차순) ➔ 봉사시작일(내림차순) 다중 정렬
df_result = filter_volunteers(
    df_all,
    locations=["서울", "경기"],
    adult_posbl=True,
    sort_by=["noticeEndde", "progrmBgnde"],
    ascending=[True, False]
)

# 지역명 ↔ 코드 상호 변환
sido_cd, gugun_cd = get_area_code("서울 강남구")  # ➔ ('6110000', '3220000')
loc_name = get_location_name("6480000", "5370000") # ➔ '경상남도 거제시'
```

---

## 📋 4. 데이터 칼럼 명세서 & API 사양 (Data Dictionary)

### 1365 Open API 주요 오퍼레이션
- **Base URL**: `http://apis.data.go.kr/1741000/volunteerPartcptnService`
- **`getVltrSearchWordList`**: 봉사참여정보 목록 조회 (요약 API)
- **`getVltrPartcptnItem`**: 봉사참여정보 상세 정보 조회 (상세 API)

### XML 주요 칼럼(태그) 명세서
| 영문 칼럼명 | 한글 명칭 | 설명 및 반환 형태 예시 |
| :--- | :--- | :--- |
| `progrmRegistNo` | **프로그램 등록번호** | 봉사활동 고유 식별 ID (예: `3510510`) |
| `progrmSj` | **봉사 제목** | 봉사활동 프로그램 제목 |
| `progrmSttusSe` | **모집 상태 코드** | `1`: 모집전, `2`: 모집중, `3`: 모집마감 |
| `progrmBgnde` | **봉사 시작일** | YYYYMMDD (예: `20260902`) |
| `progrmEndde` | **봉사 종료일** | YYYYMMDD (예: `20260902`) |
| `noticeBgnde` | **모집 시작일** | YYYYMMDD (예: `20260826`) |
| `noticeEndde` | **모집 종료일** | YYYYMMDD (예: `20260901`) |
| `actBeginTm` | **활동 시작 시간** | 시 단위 (예: `9` ➔ 09시) |
| `actEndTm` | **활동 종료 시간** | 시 단위 (예: `15` ➔ 15시) |
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
| `sidoCd` | **시도 코드** | 행정구역 시도 코드 (예: `6110000`) |
| `gugunCd` | **시군구 코드** | 행정구역 시군구 코드 (예: `3220000`) |
| `srvcClCode` | **봉사 분야** | 서비스 분류 (예: `재난ㆍ재해`, `행정보조` 등) |
| `postAdres` | **우편 주소** | 상세 봉사 장소 주소 |
| `telno` | **전화번호** | 담당자 / 센터 연락처 |
| `email` | **이메일** | 담당자 이메일 주소 |
| `progrmCn` | **봉사 상세 내용** | 봉사활동 상세 모집요강 및 준비물 |

---

## 💻 5. 개발자 가이드 & 언어별 호출 샘플 (Code Samples)

### 1. Python (파이썬)
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

### 2. cURL
```bash
curl -X GET "http://apis.data.go.kr/1741000/volunteerPartcptnService/getVltrSearchWordList?serviceKey=YOUR_SERVICE_KEY&numOfRows=10&pageNo=1"
```

---

## 📁 파일 구조 (Directory Structure)

```text
c:\dev_project\1365\
├── index.html               # 💻 반응형 웹 탐색기 대시보드 UI
├── area_mapper.js           # 🗺️ JS Area Mapper 엔진 (194개 지자체, 요일/D-Day 계산)
├── area_mapper.py           # 🐍 파이썬 시도/시군구 자동 매칭 모듈
├── volunteer_search.py      # 🐍 파이썬 2단계 파이프라인 수집/필터링 엔진
├── server.py                # 🔒 로컬 백엔드 프록시 서버 (PORT 3000)
├── fetch_volunteer_data.ipynb # 📓 데이터 분석 탐색용 Jupyter Notebook
├── .env                     # 🔒 API 인증키 환경변수 파일 (SERVICE_KEY)
└── README.md                # 📄 본 프로젝트 명세 가이드 문서
```
