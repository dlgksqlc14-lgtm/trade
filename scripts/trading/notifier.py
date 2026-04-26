import os
import requests
from dotenv import load_dotenv

load_dotenv('scripts/trading/.env')


def send_alert(message: str):
    token = os.getenv('KAKAO_ACCESS_TOKEN')
    if token:
        _send_kakao(message, token)
    else:
        print(f"[ALERT] {message}")


def _send_kakao(message: str, token: str):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "template_object": {
            "object_type": "text",
            "text": message,
            "link": {"web_url": "", "mobile_web_url": ""},
        }
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print(f"[Notifier] 카카오 전송 실패: {e}")
