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
