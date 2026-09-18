# 🔒 Backend Standby Directory (백엔드 듀얼 모드 예비 폴더)

본 `backend/` 폴더는 추후 **백엔드 듀얼 모드(Dual-Mode)** 연동 및 실시간 API 프록시 서버 구축을 위한 예비 공간입니다.

---

## 📌 현재 상태 및 가이드

* **현재 운영 상태**: **비활성화 (Standby)**
* **사유**: 현재 v2.0.0 버전은 서버비 $0원 & 0.01초 초고속 속도를 자랑하는 **백엔드 제로 정적 아키텍처 (`data.json`)**로 기본 구동 중입니다.
* **추후 활용 방안**: 
  - 실시간 API 프록시 또는 회원가입/유저 DB 구축이 필요할 때 본 폴더 안의 `server.py` (또는 FastAPI / Node.js) 코드를 가동하고, `index.html`에서 `USE_BACKEND_SERVER = true`로 스위칭하여 연동할 수 있습니다.
