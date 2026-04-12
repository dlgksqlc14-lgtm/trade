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
