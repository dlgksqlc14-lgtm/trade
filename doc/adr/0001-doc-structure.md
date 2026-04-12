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
