# AI-Navigable Documentation Structure Design

## Overview

프로젝트 문서 구조를 AI 에이전트가 효과적으로 탐색하고, 사용하면서 지식이 누적/강화되는 구조로 설계한다.

## Goals

1. 세션 시작 시 AI가 관련 feature를 정확히 인지
2. Feature 작업 결과에서 재사용 가능한 패턴이 자연스럽게 승격
3. Writer/Reviewer 에이전트로 문서 품질 유지
4. AGENTS.md로 도구 중립 호환성 확보

## Directory Structure

```
CLAUDE.md                              # 전역 rule + doc/ 탐색 안내
AGENTS.md                              # 도구 중립 AI 에이전트 설정

doc/
  README.md                            # 전체 개요 + feature index (키워드 포함)
  adr/                                 # Architecture Decision Records (MADR 포맷)
    NNNN-<title>.md
  patterns/                            # feature result에서 승격된 재사용 패턴/레시피
    <pattern-name>.md
  project/
    <feature>/
      _index.md                        # 상태, 키워드, 의존성, 관련 ADR/패턴 링크
      design/                          # 설계 문서 (누적)
      plan/                            # 계획 문서 (누적)
      implement/                       # 구현 노트 (누적)
      result/                          # 결과, 회고, 패턴 후보 태깅
```

### File Naming

- 일반 문서: `YYYY-MM-DD-<short-description>.md`
- ADR: `NNNN-<title>.md` (순번)
- 패턴: `<pattern-name>.md` (의미 기반)

## AI Navigation Flow

```
세션 시작
  → CLAUDE.md 읽기 (전역 rule)
  → doc/README.md 읽기 (feature index + 키워드)
  → 현재 task와 관련된 feature 판단
    → 명확: 해당 feature의 _index.md 읽기 → 상세 문서 진입
    → 애매함: 사용자에게 "이 feature가 맞나요?" 확인
    → 새 feature: doc structure 먼저 생성
```

## Pattern Promotion Flow

```
Feature 작업 중
  → result/ 문서 작성 시 Writer Agent가 패턴 후보 태깅
    (문서 내 "## Pattern Candidate" 섹션으로 마킹)
  → Reviewer Agent가 패턴 후보 검토
    - 재사용 가능성
    - 다른 feature와의 관련성
    - 명확성/완성도
  → 사용자에게 승격 제안 제시
  → 승인 시:
    1. doc/patterns/ 에 패턴 문서 생성
    2. 원본 result 문서에 패턴 링크 추가
    3. README에 패턴 index 업데이트
```

### Pattern Document Format

```markdown
---
name: 패턴 이름
origin: <feature>/<result 문서>
date: YYYY-MM-DD
---

## Context
어떤 상황에서 이 패턴이 유용한가

## Pattern
구체적인 접근법/레시피

## Examples
적용 사례
```

## Agents

### Writer Agent

**역할**: 문서 작성/업데이트

**담당 범위:**
- feature `_index.md` 생성 및 업데이트
- `doc/README.md` feature index 업데이트
- `result/` 문서 작성 시 패턴 후보 태깅
- 패턴 승격 승인 시 `doc/patterns/` 문서 생성

**트리거:**
- `/doc-write` 커맨드로 수동 호출
- feature 완료 시 자동 실행

### Reviewer Agent

**역할**: 문서 품질/일관성 검증

**담당 범위:**
- `_index.md`와 실제 하위 문서 일치 여부
- README의 feature index가 최신 상태인지
- 패턴 후보의 재사용 가능성/명확성 검토
- ADR과 실제 구현 간 불일치 탐지

**트리거:**
- `/doc-review` 커맨드로 수동 호출
- Writer Agent 실행 후 자동 실행 (Writer → Reviewer 순서)
- feature 완료 시 자동 실행

### Execution Flow

```
수동: /doc-write → Writer Agent → Reviewer Agent
수동: /doc-review → Reviewer Agent만

Feature 완료 시:
  → Writer Agent (result 작성, _index 업데이트, 패턴 태깅)
  → Reviewer Agent (일관성 검증, 패턴 승격 제안)
  → 사용자 승인 대기
```

## CLAUDE.md / AGENTS.md Role Split

### CLAUDE.md (Claude Code 전용)

전역 rule + Claude Code 전용 기능 (커맨드, hook, 에이전트 설정):
- Session Init 절차
- Coding Conventions (Kent Beck 스타일)
- Doc Rules (누적 원칙, 명명 규칙)
- Agent 커맨드 (`/doc-write`, `/doc-review`)
- General Rules (한국어 응답)

### AGENTS.md (도구 중립)

어떤 AI 도구든 읽을 수 있는 범용 프로젝트 설정:
- 프로젝트 컨텍스트
- Session Start 절차
- Documentation 구조
- Conventions

## Design Decisions

- **ADR 도입**: feature에 종속되지 않는 프로젝트 전반 결정을 기록. MADR 포맷 채택 (업계 표준)
- **`_index.md` 패턴**: AI 네비게이션 진입점. Feature-Sliced Design에서 차용
- **AGENTS.md 추가**: 2025년 Linux Foundation 표준. 도구 중립 호환성 확보
- **Pattern promotion**: 자동 추상화 대신 사용자 승인 기반. Kent Beck "3번 반복 후 추상화" 원칙의 변형
- **Writer/Reviewer 분리**: 작성과 검증의 관심사 분리. 단독 실행도 가능
