# config/settings.py
# 브로커 설정 — 계정 정보는 .env 파일에서 로드 (GitHub 비공개)

import os
from dotenv import load_dotenv

# .env 파일 로드 (config/ 폴더 안의 .env)
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

# ================================
# 브로커 설정
# ================================
BROKERS = {
    "Zero Markets": {
        "login":    int(os.getenv("ZERO_LOGIN", "0")),
        "password": os.getenv("ZERO_PASSWORD", ""),
        "server":   os.getenv("ZERO_SERVER", ""),
        "path":     os.getenv("ZERO_PATH", ""),
        "type":     "mt5",
    },
}
