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
