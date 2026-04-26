#!/bin/bash
# 사용법: ./scripts/trading/deploy.sh <EC2_PUBLIC_IP> <KEY_PEM_PATH>
set -e

EC2_IP=$1
KEY=$2

if [ -z "$EC2_IP" ] || [ -z "$KEY" ]; then
  echo "Usage: $0 <EC2_IP> <KEY_PEM>"
  echo ""
  echo "Example: $0 13.125.100.200 ~/.ssh/trade-key.pem"
  exit 1
fi

echo "=== 코드 전송 중... ==="
rsync -avz \
  --exclude '.env' \
  --exclude '__pycache__' \
  --exclude 'state.json' \
  --exclude 'emergency_close.flag' \
  --exclude '.venv' \
  -e "ssh -i $KEY -o StrictHostKeyChecking=no" \
  scripts/trading/ ubuntu@$EC2_IP:~/trading/
rsync -avz -e "ssh -i $KEY -o StrictHostKeyChecking=no" \
  scripts/__init__.py scripts/trading/__init__.py ubuntu@$EC2_IP:~/scripts/trading/ 2>/dev/null || true
rsync -avz -e "ssh -i $KEY -o StrictHostKeyChecking=no" \
  tests/ ubuntu@$EC2_IP:~/tests/

echo "=== 의존성 설치 중... ==="
ssh -i $KEY ubuntu@$EC2_IP "
  sudo apt-get update -q
  sudo apt-get install -y python3-pip python3-venv screen -q
  cd ~ && python3 -m venv venv
  ~/venv/bin/pip install -r ~/trading/requirements.txt -q
"

echo ""
echo "✅ 배포 완료!"
echo ""
echo "다음 단계:"
echo "  1. .env 파일 전송 (API 키 포함):"
echo "     scp -i $KEY scripts/trading/.env ubuntu@$EC2_IP:~/trading/.env"
echo ""
echo "  2. EC2 접속:"
echo "     ssh -i $KEY ubuntu@$EC2_IP"
echo ""
echo "  3. 스케줄러 실행:"
echo "     screen -S trader"
echo "     ~/venv/bin/python ~/trading/scheduler.py"
echo "     (Ctrl+A, D 로 detach)"
echo ""
echo "  4. 대시보드 실행:"
echo "     screen -S dashboard"
echo "     ~/venv/bin/python ~/trading/dashboard.py"
echo "     접속: http://$EC2_IP:8080"
