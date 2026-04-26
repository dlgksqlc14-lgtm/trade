---
feature: auto-trading-system
status: in-progress
keywords: trading, backtest, signal, BNF, deviation-rate, KRX, binance, scheduler, dashboard
dependencies: []
related_adr: []
related_patterns: []
---

# Auto Trading System

BNF 이격도 기반 역추세 자동매매 시스템.

## 개요

Signal Engine이 이격도를 계산해 시그널을 생성하고, Order Manager가 포지션을 관리하며 거래소 API에 주문을 전송한다. Scheduler가 전체 파이프라인을 주기적으로 실행하고, FastAPI 대시보드가 현황을 표시한다.

## 단계

- **Phase 1**: 백테스트로 전략 수익성 검증
- **Phase 2**: KIS(KRX) + Binance 실거래 자동화
- **Phase 3**: FastAPI 대시보드 + AWS EC2 배포

## 문서

| 종류 | 파일 |
|------|------|
| 설계 | `docs/superpowers/specs/2026-04-26-auto-trading-system-design.md` |
| 계획 | `docs/superpowers/plans/2026-04-26-auto-trading-system.md` |
