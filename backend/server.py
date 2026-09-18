"""
[NOTE] 백엔드 듀얼 모드 예비용 서버 코드 (Standby Backend Server)
현재 v2.0.0 버전은 백엔드 없는 정적 모드(data.json)로 기본 작동 중입니다.
추후 실시간 API 프록시나 백엔드 연동이 필요할 때 본 서버 코드를 활용/실행할 수 있습니다.
"""

import os, json
import sys
import urllib.request
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 3000
BASE_URL = "https://apis.data.go.kr/1741000/volunteerPartcptnService"

def load_env():
    """Load variables from .env file"""
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

class ProxyHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        # API Proxy endpoint
        if parsed_path.path.startswith("/api/volunteer"):
            query_params = urllib.parse.parse_qs(parsed_path.query)
            op = query_params.get("op", ["getVltrSearchWordList"])[0]
            
            # Forward all query parameters to target API
            target_params = {"serviceKey": SERVICE_KEY}
            for k, v in query_params.items():
                if k != "op" and v:
                    target_params[k] = v[0]
                
            target_url = f"{BASE_URL}/{op}?{urllib.parse.urlencode(target_params)}"
            
            try:
                req = urllib.request.Request(target_url, headers={"User-Agent": "Mozilla/5.0"})
                # Increase timeout to 30s for large 10,000 item downloads
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = resp.read()
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/xml; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(data)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                err_msg = json.dumps({"error": str(e)}).encode("utf-8")
                self.wfile.write(err_msg)
            return

        return super().do_GET()

def run(server_class=HTTPServer, handler_class=ProxyHandler):
    print(f"[1365 Backend Proxy Server] Running on http://localhost:{PORT}")
    print(f"Using SERVICE_KEY from .env: {SERVICE_KEY[:6]}...{SERVICE_KEY[-4:]}")
    httpd = server_class(("", PORT), handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run()
