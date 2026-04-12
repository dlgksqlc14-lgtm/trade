# Doc Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AI가 효과적으로 탐색하고, 사용하면서 지식이 누적/강화되는 문서 구조를 구축한다.

**Architecture:** CLAUDE.md(전역 rule) → doc/README.md(feature index) → _index.md(feature 진입점) 3단계 탐색 구조. Writer/Reviewer 에이전트를 .claude/commands/로 구현하여 /doc-write, /doc-review 커맨드로 호출.

**Tech Stack:** Markdown, Claude Code custom commands (.claude/commands/)

---

## File Structure

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `doc/adr/` | ADR 디렉토리 |
| Create | `doc/patterns/` | 패턴 디렉토리 |
| Create | `doc/adr/0001-doc-structure.md` | 첫 번째 ADR: 이 문서 구조 결정 기록 |
| Create | `doc/project/doc-structure/_index.md` | doc-structure feature 진입점 |
| Modify | `doc/README.md` | 키워드 기반 feature index로 강화 |
| Modify | `CLAUDE.md` | Session Init 절차 강화 + Agent 커맨드 안내 |
| Create | `AGENTS.md` | 도구 중립 AI 에이전트 설정 |
| Create | `.claude/commands/doc-write.md` | Writer Agent 커맨드 |
| Create | `.claude/commands/doc-review.md` | Reviewer Agent 커맨드 |

---

## Task 1: 디렉토리 구조 생성

**Files:**
- Create: `doc/adr/` (directory)
- Create: `doc/patterns/` (directory)

- [ ] **Step 1: 디렉토리 생성**

```bash
mkdir -p doc/adr doc/patterns
```

- [ ] **Step 2: 디렉토리 존재 확인**

Run: `ls -d doc/adr doc/patterns`
Expected: 두 디렉토리 모두 출력

- [ ] **Step 3: Commit**

```bash
git add doc/adr/.gitkeep doc/patterns/.gitkeep
git commit -m "chore: add adr and patterns directories"
```

Note: 빈 디렉토리를 git에 추적하기 위해 `.gitkeep` 파일 필요

```bash
touch doc/adr/.gitkeep doc/patterns/.gitkeep
```

---

## Task 2: 첫 번째 ADR 작성

**Files:**
- Create: `doc/adr/0001-doc-structure.md`

- [ ] **Step 1: ADR 작성**

```markdown
# 1. AI-Navigable Documentation Structure 채택

## Status

Accepted

## Context

프로젝트 문서가 늘어나면서 AI 에이전트가 세션 시작 시 관련 feature를 정확히 인지하지 못하는 문제가 발생했다. 특히 feature가 README에 등록되어 있어도 해당 feature의 상세 문서까지 자동으로 읽지 않았다.

또한 feature 작업 중 얻은 교훈이 다른 feature에서 재사용되지 않고 사라지는 문제가 있었다.

## Decision

다음 구조를 채택한다:

- `CLAUDE.md` → `doc/README.md` → `_index.md` 3단계 AI 탐색 흐름
- `doc/adr/`: 프로젝트 전반 결정 기록 (MADR 포맷)
- `doc/patterns/`: feature result에서 승격된 재사용 패턴
- `doc/project/<feature>/_index.md`: AI 네비게이션 진입점
- `AGENTS.md`: 도구 중립 AI 에이전트 설정
- Writer/Reviewer Agent로 문서 품질 유지

## Consequences

- AI 에이전트가 세션 시작 시 관련 feature를 3단계로 정확히 탐색 가능
- 패턴 승격 흐름으로 지식이 누적됨
- AGENTS.md로 Claude Code 외 다른 AI 도구와도 호환
- 문서 관리 포인트가 늘어남 (README, _index.md, ADR, patterns)
- Writer/Reviewer Agent 유지보수 필요
```

- [ ] **Step 2: Commit**

```bash
git add doc/adr/0001-doc-structure.md
git commit -m "docs: add ADR-0001 for doc structure decision"
```

---

## Task 3: doc/project/doc-structure/_index.md 작성

**Files:**
- Create: `doc/project/doc-structure/_index.md`

- [ ] **Step 1: _index.md 작성**

```markdown
---
feature: doc-structure
status: in-progress
keywords: [documentation, AI navigation, agent, pattern, ADR]
dependencies: []
related_adr: [0001-doc-structure]
related_patterns: []
---

# doc-structure

AI 에이전트가 효과적으로 탐색하고, 사용하면서 지식이 누적/강화되는 문서 구조.

## Summary

- CLAUDE.md → README → _index.md 3단계 AI 탐색 흐름
- doc/adr/: 프로젝트 전반 결정 기록
- doc/patterns/: feature result에서 승격된 패턴
- Writer/Reviewer Agent로 문서 품질 유지

## Documents

### design/
- [2026-04-12-doc-structure-design.md](design/2026-04-12-doc-structure-design.md) — 전체 설계

### plan/
- [2026-04-12-implementation-plan.md](plan/2026-04-12-implementation-plan.md) — 구현 계획

### implement/
(아직 없음)

### result/
(아직 없음)
```

- [ ] **Step 2: Commit**

```bash
git add doc/project/doc-structure/_index.md
git commit -m "docs: add _index.md for doc-structure feature"
```

---

## Task 4: doc/README.md 키워드 기반 feature index로 강화

**Files:**
- Modify: `doc/README.md` (currently `doc/project/README.md`)

Note: 현재 README.md는 `doc/project/README.md`에 있다. 스펙에 따르면 `doc/README.md`가 맞으므로 이동한다.

- [ ] **Step 1: README.md를 doc/ 루트로 이동**

```bash
mv doc/project/README.md doc/README.md
```

- [ ] **Step 2: README.md 내용 업데이트**

```markdown
# Project Overview

스크립트 기반 프로젝트. 다양한 기능을 독립적인 스크립트로 구현하고, 각 기능별 문서를 체계적으로 관리한다.

## Feature Index

| Feature | Status | Keywords | Description |
|---------|--------|----------|-------------|
| [doc-structure](project/doc-structure/_index.md) | in-progress | documentation, AI navigation, agent, pattern, ADR | AI-navigable 문서 구조 설계 및 구축 |

## ADR Index

| # | Title | Status |
|---|-------|--------|
| [0001](adr/0001-doc-structure.md) | AI-Navigable Documentation Structure 채택 | Accepted |

## Pattern Index

| Pattern | Origin | Description |
|---------|--------|-------------|
| *(아직 등록된 pattern 없음)* | - | - |

## How to Add a New Feature

1. `doc/project/<feature-name>/` 디렉토리 생성
2. 하위에 `design/`, `plan/`, `implement/`, `result/` 디렉토리 생성
3. `_index.md` 작성 (frontmatter에 keywords, status, dependencies 포함)
4. 위 Feature Index 테이블에 등록
5. design 문서 작성 후 구현 시작
```

- [ ] **Step 3: Commit**

```bash
git add doc/README.md
git rm doc/project/README.md 2>/dev/null || true
git commit -m "docs: move README.md to doc/ root and add keyword-based feature index"
```

---

## Task 5: CLAUDE.md 업데이트

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: CLAUDE.md 전체 내용 교체**

```markdown
# Project Rules

## Session Init

세션 시작 시 반드시 다음 순서를 따른다:

1. 이 파일을 읽는다
2. `doc/README.md`를 읽어 feature index와 키워드를 파악한다
3. 현재 task/질문의 키워드와 feature index를 대조하여 관련 feature를 판단한다
   - **명확한 경우**: 해당 feature의 `doc/project/<feature>/_index.md`를 읽고, 필요한 상세 문서로 진입한다
   - **애매한 경우**: 사용자에게 "이 feature가 맞나요?"라고 확인한다
   - **새 feature인 경우**: doc structure를 먼저 생성한다 (How to Add a New Feature 참고)
4. 관련 ADR과 패턴이 있으면 함께 참고한다

## Documentation Structure

모든 프로젝트 문서는 `doc/` 하위에 위치한다:

```
doc/
  README.md                            # 전체 개요 + feature/ADR/pattern index
  adr/                                 # Architecture Decision Records (MADR)
  patterns/                            # feature result에서 승격된 패턴
  project/
    <feature>/
      _index.md                        # 상태, 키워드, 의존성, 관련 ADR/패턴
      design/                          # 설계 문서 (누적)
      plan/                            # 계획 문서 (누적)
      implement/                       # 구현 노트 (누적)
      result/                          # 결과, 회고, 패턴 후보 태깅
```

### Doc Rules

- 문서는 누적한다 -- 덮어쓰기 금지
- 파일 명명: `YYYY-MM-DD-<short-description>.md`
- ADR 명명: `NNNN-<title>.md`
- 새 feature 시작 시 doc structure를 먼저 생성한다

## Coding Conventions (Kent Beck Style)

- **Simple Design**: code passes all tests, reveals intention, has no duplication, fewest elements
- **Small methods**: each method does one thing, named clearly for what it does
- **No premature abstraction**: duplication is cheaper than wrong abstraction -- wait for 3 occurrences
- **Test first**: write failing test, make it pass, refactor
- **Incremental change**: small commits, each one leaving the code better than before
- **Clear naming**: names tell the reader what, not how. Avoid abbreviations
- **Flat over nested**: prefer early returns, avoid deep nesting
- **Composition over inheritance**

## Script Project Conventions

- Scripts live in `scripts/` directory
- Each script is self-contained and executable
- Include usage/help output when run without arguments
- Use clear exit codes (0 = success, 1 = error)

## Agents

문서 관리를 위한 에이전트 커맨드:

- `/doc-write`: Writer Agent 호출 -- 문서 작성/업데이트, 패턴 후보 태깅
- `/doc-review`: Reviewer Agent 호출 -- 문서 일관성 검증, 패턴 승격 제안

Feature 완료 시 `/doc-write` → `/doc-review` 순서로 실행한다.

## General Rules

- 한국어로 응답한다
- 기존 doc을 참조한 뒤 작업을 시작한다
- 코드는 단순하게 -- 복잡성은 최후의 수단이다
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with enhanced session init and agent commands"
```

---

## Task 6: AGENTS.md 작성

**Files:**
- Create: `AGENTS.md`

- [ ] **Step 1: AGENTS.md 작성**

```markdown
# Project Agent Instructions

## Context

스크립트 기반 프로젝트. 다양한 기능을 독립적인 스크립트로 구현하고, 각 기능별 문서를 체계적으로 관리한다.

## Session Start

1. `doc/README.md`를 읽어 feature index와 키워드를 파악한다
2. 현재 task의 키워드와 feature index를 대조하여 관련 feature를 판단한다
   - 명확하면: `doc/project/<feature>/_index.md`를 읽고 상세 문서로 진입
   - 애매하면: 사용자에게 확인
   - 새 feature면: doc structure 먼저 생성
3. 관련 ADR(`doc/adr/`)과 패턴(`doc/patterns/`)을 참고한다

## Documentation

```
doc/
  README.md              # Feature/ADR/Pattern index
  adr/                   # Architecture Decision Records
  patterns/              # 승격된 재사용 패턴
  project/<feature>/     # Feature별 문서
    _index.md            # 진입점 (상태, 키워드, 의존성)
    design/              # 설계 문서
    plan/                # 계획 문서
    implement/           # 구현 노트
    result/              # 결과, 회고
```

### Rules

- 문서는 누적한다 (덮어쓰기 금지)
- 파일 명명: `YYYY-MM-DD-<short-description>.md`
- 새 feature 시작 시 doc structure 먼저 생성

## Conventions

- 한국어로 응답
- Kent Beck 스타일: 단순 설계, 작은 메서드, TDD, 점진적 변경
- 복잡성은 최후의 수단
```

- [ ] **Step 2: Commit**

```bash
git add AGENTS.md
git commit -m "docs: add AGENTS.md for tool-agnostic AI agent instructions"
```

---

## Task 7: Writer Agent 커맨드 작성

**Files:**
- Create: `.claude/commands/doc-write.md`

- [ ] **Step 1: commands 디렉토리 생성**

```bash
mkdir -p .claude/commands
```

- [ ] **Step 2: doc-write.md 작성**

```markdown
# Writer Agent

문서 작성/업데이트를 수행하는 에이전트.

## Instructions

다음 작업을 순서대로 수행하라:

### 1. 현재 상태 파악

- `doc/README.md`를 읽어 feature index를 확인한다
- 현재 작업 중인 feature의 `_index.md`를 읽는다
- feature 디렉토리의 실제 문서 목록을 확인한다

### 2. _index.md 업데이트

- `_index.md`의 Documents 섹션이 실제 파일과 일치하는지 확인한다
- 새로 추가된 문서가 있으면 Documents 섹션에 추가한다
- frontmatter의 status, keywords, dependencies를 최신 상태로 갱신한다

### 3. README.md 업데이트

- `doc/README.md`의 Feature Index가 최신 상태인지 확인한다
- feature의 status나 keywords가 변경되었으면 반영한다
- 새로운 ADR이 있으면 ADR Index에 추가한다

### 4. 패턴 후보 탐지

- `result/` 디렉토리의 문서를 확인한다
- 다른 feature에서 재사용할 수 있는 접근법이 있으면 `## Pattern Candidate` 섹션을 추가한다
- 패턴 후보에는 다음을 포함한다:
  - **Name**: 패턴 이름
  - **Context**: 어떤 상황에서 유용한가
  - **Pattern**: 구체적인 접근법
  - **Reusability**: 왜 다른 feature에서도 유용한가

### 5. 패턴 승격 (사용자 승인 시)

사용자가 패턴 승격을 승인하면:
1. `doc/patterns/<pattern-name>.md` 생성 (frontmatter 포함)
2. 원본 result 문서에 패턴 링크 추가
3. `doc/README.md`의 Pattern Index에 추가

### 6. 결과 보고

수행한 변경사항을 요약하여 보고한다.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/doc-write.md
git commit -m "feat: add /doc-write Writer Agent command"
```

---

## Task 8: Reviewer Agent 커맨드 작성

**Files:**
- Create: `.claude/commands/doc-review.md`

- [ ] **Step 1: doc-review.md 작성**

```markdown
# Reviewer Agent

문서 품질/일관성을 검증하는 에이전트.

## Instructions

다음 검증을 순서대로 수행하라:

### 1. 구조 일관성 검증

- `doc/README.md`의 Feature Index에 등록된 모든 feature가 실제로 존재하는지 확인한다
- 각 feature 디렉토리에 `_index.md`가 있는지 확인한다
- `_index.md`의 Documents 섹션이 실제 파일과 일치하는지 확인한다

### 2. Feature Index 검증

- `doc/README.md`의 Feature Index에서:
  - status가 _index.md의 frontmatter와 일치하는지
  - keywords가 _index.md와 일치하는지
  - 링크가 유효한지

### 3. ADR 검증

- `doc/adr/`의 ADR 목록이 README의 ADR Index와 일치하는지
- ADR 번호가 순차적인지
- feature의 `_index.md`에서 참조하는 ADR이 실제로 존재하는지

### 4. 패턴 후보 검토

- `result/` 문서에서 `## Pattern Candidate` 섹션을 탐색한다
- 각 패턴 후보에 대해 다음을 평가한다:
  - **재사용 가능성**: 다른 feature에서 실제로 쓸 수 있는가?
  - **명확성**: 패턴 설명이 충분히 구체적인가?
  - **완성도**: Context, Pattern, Examples가 모두 있는가?
- 승격할 만한 패턴이 있으면 사용자에게 제안한다:
  - 패턴 이름, 요약, 승격 이유를 제시
  - 사용자 승인을 기다린다

### 5. 결과 보고

검증 결과를 다음 형식으로 보고한다:

```
## Review Result

### Passed
- (통과한 항목)

### Issues Found
- (발견된 문제와 수정 제안)

### Pattern Promotion Candidates
- (승격 제안할 패턴, 없으면 "없음")
```
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/doc-review.md
git commit -m "feat: add /doc-review Reviewer Agent command"
```

---

## Task 9: 전체 통합 검증

- [ ] **Step 1: 디렉토리 구조 확인**

Run: `find doc/ -type f | sort`
Expected:
```
doc/README.md
doc/adr/0001-doc-structure.md
doc/adr/.gitkeep
doc/patterns/.gitkeep
doc/project/doc-structure/_index.md
doc/project/doc-structure/design/2026-04-12-doc-structure-design.md
doc/project/doc-structure/plan/2026-04-12-implementation-plan.md
```

- [ ] **Step 2: CLAUDE.md Session Init 절차 확인**

CLAUDE.md를 읽고 Session Init 섹션에 3단계 탐색 흐름이 명시되어 있는지 확인한다.

- [ ] **Step 3: AGENTS.md 존재 확인**

Run: `cat AGENTS.md | head -5`
Expected: `# Project Agent Instructions` 헤더

- [ ] **Step 4: Agent 커맨드 확인**

Run: `ls .claude/commands/`
Expected: `doc-review.md  doc-write.md`

- [ ] **Step 5: /doc-review 실행하여 전체 일관성 테스트**

`/doc-review` 커맨드를 실행하여 Reviewer Agent가 모든 검증을 통과하는지 확인한다.

- [ ] **Step 6: 최종 Commit**

```bash
git add -A
git commit -m "docs: complete doc-structure feature implementation"
```
