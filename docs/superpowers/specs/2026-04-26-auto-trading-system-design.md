# Auto Trading System — Design Spec

**Date**: 2026-04-26  
**Status**: Draft  
**Author**: brainstorming session

---

## Overview

BNF 스타일 이격도(Deviation Rate) 기반 역추세 자동매매 시스템.  
한국 주식(KRX)과 암호화폐(Crypto) 두 시장을 대상으로, 완전 자동 주문 실행과 웹 대시보드 모니터링을 제공한다.

---

## 1. 트레이딩 전략

### 핵심 원리

이격도(Deviation Rate) = (현재가 / N일 이동평균) × 100 - 100

주가가 이동평균선에서 과도하게 이탈하면 평균으로 회귀하는 성질(Mean Reversion)을 이용한다.

**학술 근거**
- Poterba & Summers (1988) — 주가의 평균회귀 실증
- Bollinger Bands (John Bollinger) — 통계적 이탈 기반 매매
- Wilder RSI (1978) — 과매도 구간 매수의 체계화

---

### 한국 주식 (KRX) 매매 규칙

| 신호 | 조건 |
|------|------|
| 매수 | 25일 MA 이격률 ≤ -10% |
| 추가 매수 | 이격률 ≤ -15% (1회 한정) |
| 매도 | 이격률 ≥ -2% |
| 손절 | 이격률 ≤ -25% 또는 매입가 대비 -20% |

**필터 조건**
- 거래량이 20일 평균 거래량의 150% 이상일 때만 시그널 유효
- 코스피 지수 당일 -3% 이상 급락 중이면 신규 매수 보류
- 시가총액 1,000억 원 이상 종목만 대상

---

### 암호화폐 (Crypto) 매매 규칙

| 신호 | 조건 |
|------|------|
| 매수 | 24시간봉 20일 MA 이격률 ≤ -12% |
| 추가 매수 | 이격률 ≤ -20% (1회 한정) |
| 매도 | 이격률 ≥ -3% |
| 손절 | 이격률 ≤ -30% |

**대상 종목**: BTC/USDT, ETH/USDT 등 시총 상위 5~10개 (소형 알트코인 제외)

---

### 포지션 사이징

- 1회 매매 금액: 총 자산의 20~25%
- 최대 동시 보유 포지션: 4개
- 추가 매수 금액: 기존 포지션 금액의 50%

### 리스크 관리

- 일일 최대 손실 한도: 총 자산의 5% 초과 시 당일 매매 자동 중단
- API 오류 발생 시 카카오톡/이메일 즉시 알림
- 대시보드에 전체 포지션 즉시 청산 버튼 제공

---

## 2. 시스템 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                    Scheduler                         │
│         (매 1분/5분/1일 주기로 파이프라인 실행)          │
└──────────────────────┬──────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │     Data Collector      │
          │  KIS API / ccxt         │
          │  현재가, 거래량, OHLCV   │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │    Signal Engine        │
          │  이격도 계산              │
          │  매수/매도/손절 시그널     │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │    Order Manager        │
          │  포지션 관리              │
          │  주문 실행 (KIS / ccxt)  │
          │  손절/익절 자동 처리      │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │    Web Dashboard        │
          │  현재 포지션, 수익률       │
          │  시그널 로그              │
          │  (FastAPI + Jinja2)     │
          └─────────────────────────┘
```

### 모듈별 책임

| 모듈 | 역할 | 주요 라이브러리 |
|------|------|----------------|
| Scheduler | 주기적 파이프라인 실행 | `APScheduler` |
| Data Collector | 시세/OHLCV 수집 | `pykis`, `ccxt` |
| Signal Engine | 이격도 계산 + 시그널 생성 | `pandas`, `ta` |
| Order Manager | 주문 실행 + 포지션 추적 | `pykis`, `ccxt` |
| Web Dashboard | 모니터링 UI | `FastAPI`, `Jinja2` |

### 실행 타이밍

| 주기 | 작업 |
|------|------|
| 매 1분 | 암호화폐 현재가 체크, 손절/익절 감시 |
| 매 5분 | 암호화폐 시그널 재계산 |
| 장중 09:05~15:20, 매 10분 | 한국 주식 현재가 + 시그널 체크 |
| 매일 16:00 | 한국 주식 일봉 수집 + 다음날 시그널 준비 |

---

## 3. 프로젝트 구조

```
scripts/
  trading/
    collector.py      # 데이터 수집
    signal.py         # 이격도 시그널 엔진
    order.py          # 주문 실행
    scheduler.py      # 메인 실행 루프
    dashboard.py      # 웹 대시보드
    backtest.py       # 백테스트
    config.yaml       # 전략 파라미터 설정 (git 포함)
    .env              # API 키 (git 제외, .gitignore에 추가)
```

---

## 4. 셋업 체크리스트

### 계좌 및 API

- [ ] 한국투자증권 계좌 개설
- [ ] KIS Developers 가입 → App Key / App Secret 발급 (https://apiportal.koreainvestment.com)
- [ ] KIS 모의투자 신청
- [ ] Binance 계좌 개설 + API Key 발급 (거래 권한 활성화)
- [ ] Binance 테스트넷 API Key 발급

### 개발 환경

```bash
pip install pykis ccxt pandas ta fastapi uvicorn apscheduler pyyaml python-dotenv requests
```

- `python-dotenv` — .env에서 API 키 로드
- `requests` — 카카오톡 알림 API 호출

### 인프라

| 단계 | 플랫폼 | 비용 |
|------|--------|------|
| Phase 1~2 (백테스트/모의투자) | 로컬 맥 | 무료 |
| Phase 3 실투자 | AWS t3.micro 서울 (ap-northeast-2) | 첫 1년 무료 → 이후 ~$9/월 |
| 1년 후 비용 절감 시 | Oracle Cloud Free (도쿄 리전) | 영구 무료 |

---

## 5. 개발 단계 (Phase Plan)

### Phase 1 — 백테스트 (2~3주)
- 과거 데이터(KRX 3년, Crypto 2년)로 전략 검증
- 파라미터 최적화 (이격도 임계값, 손절 기준)
- 수익률, 최대 낙폭(MDD), 승률 측정

### Phase 2 — 모의투자 연동 (1~2주)
- KIS 모의투자 API + Binance 테스트넷 연동
- 실제 주문 흐름 검증
- 대시보드 기본 구현

### Phase 3 — 소액 실투자
- 10~50만원으로 실전 시작
- AWS Seoul 배포
- 알림 시스템 구축 후 운영 시작

---

## 6. 기술 스택 요약

| 항목 | 선택 |
|------|------|
| 언어 | Python 3.11+ |
| 한국 주식 API | 한국투자증권 KIS (pykis) |
| 암호화폐 API | ccxt (Binance) |
| 데이터 처리 | pandas, ta |
| 스케줄러 | APScheduler |
| 웹 대시보드 | FastAPI + Jinja2 |
| 알림 | 카카오톡 REST API (또는 Telegram Bot) |
| 운영 서버 | AWS t3.micro (ap-northeast-2) |
