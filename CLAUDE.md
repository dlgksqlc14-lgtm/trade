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
