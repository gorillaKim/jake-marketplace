---
name: librarian
description: 옵시디언 CLI 기반 문서 탐색 사서. 정보 검색, 문서 최신화, 발견성 개선, 문서 생성 지원 (사서, librarian, 문서 찾기, 정보 탐색, 문서 검색, 문서 최신화, 문서 업데이트, 문서 있어, 문서 어디, docs, 매뉴얼, 가이드, 참고 문서, 정보 어디, 기록이 있, 문서 생성, 문서 작성)
---

# 사서 (Librarian)

obs-nexus CLI를 활용한 문서 탐색 및 관리 스킬입니다.
**2단계 구조**: 단순 검색은 obs-nexus CLI로 직접, 복잡한 작업은 서브에이전트로 처리합니다.

## 입력

- `args`: 검색할 질의 또는 명령
- `--team`: 팀원 모드 (세션 동안 상주)

예시:
```
/obs-nexus:librarian 검색 시스템 아키텍처
/obs-nexus:librarian --team
/obs-nexus:librarian 문서 최신화해줘
```

## CLI 참조

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` 참조

## 실행 절차

### Step 0: MCP / CLI 감지

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` — "공통 패턴 > MCP / CLI / 설치 안내 3단계 감지" 절차를 따릅니다.

### Step 1: 직접 검색 (서브에이전트 불필요)

Step 0에서 확인한 MODE에 따라 검색합니다.

**탐색 전략 우선순위**:
1. 특정 문서 경로를 알고 있다면 → `graph related` 먼저 (링크 구조 + 태그 기반, 관계 탐색에 최적)
2. 키워드로 문서를 특정하기 어렵다면 → `search` (fallback)

**MODE=mcp**:

_경로 아는 경우 (graph 우선)_:
- `nexus_find_related(project, path, k=10)` 직접 호출
- 필요 시 `nexus_get_cluster(project, path, depth=2)` 로 클러스터 확장
- 결과 있으면 `nexus_get_section(path, heading_path)` 로 섹션 추출

_키워드 검색 (fallback)_:
- `nexus_search(query, project, mode="hybrid", limit=5)` 호출
- 결과 있으면 `nexus_get_toc(path)` → `nexus_get_section(path, heading_path)` (TOC 2단계 패턴)
- 목록만 확인할 때는 `enrich=false, limit=3` 으로 토큰 절약

**MODE=cli**:

_경로 아는 경우 (graph 우선)_:
```bash
obs-nexus graph related <PROJECT> "<PATH>" --format json
# 필요 시 클러스터 확장
obs-nexus graph cluster <PROJECT> "<PATH>" --depth 2 --format json
```

_키워드 검색 (fallback)_:
```bash
obs-nexus search "<질의>" --project <ID> --mode hybrid --limit 5 --format json
```
- 결과 있으면 `obs-nexus doc section`으로 관련 섹션 추출

결과를 사용자에게 직접 전달 → **완료**

### Step 2: 서브에이전트 스폰 (검색 실패 또는 문서 관리 필요 시)

다음 상황에서만 librarian 서브에이전트를 스폰합니다:

**검색 실패 시:**
```
Agent(
  subagent_type: "obs-nexus:librarian",
  model: "haiku",
  prompt: "검색 질의: '{질의}'. 직접 검색 결과 없음. nexus 프로젝트 ID: {id}. Phase A부터 심층 검색 및 발견성 개선을 진행하세요.",
  description: "사서 심층 검색"
)
```

**문서 최신화 요청 시:**
```
Agent(
  subagent_type: "obs-nexus:librarian",
  model: "haiku",
  prompt: "문서 최신화 요청: '{문서 경로}'. nexus 프로젝트 ID: {id}. Phase C를 실행하세요.",
  description: "사서 문서 최신화"
)
```

**문서 생성 요청 시:**
```
Agent(
  subagent_type: "obs-nexus:librarian",
  model: "haiku",
  prompt: "문서 생성 요청: '{주제}'. nexus 프로젝트 ID: {id}. Phase D를 실행하세요. 현재 작업 경로: {cwd}",
  description: "사서 문서 생성"
)
```

### Step 3: 팀원 모드 (--team)

`--team` 인자가 있으면 세션 동안 상주하는 팀원으로 운영합니다:

```
1. TeamCreate(name: "librarian", description: "옵시디언 문서 탐색 사서")
2. 이후 문서 관련 질의를 SendMessage로 librarian에게 라우팅
3. "사서 해고" / "librarian 종료" 시 TeamDelete(name: "librarian")
```

## 자동 트리거 가이드

이 스킬은 다음 사용자 발화에서 자동으로 고려됩니다:

**검색/조회:**
- "~에 대한 문서 있어?" / "~ 문서 찾아줘"
- "~ 어디에 정리되어 있어?" / "~ 참고 문서"
- "매뉴얼" / "가이드" / "docs"

**문서 관리:**
- "문서 최신화해줘" / "이 문서 내용이 오래됐어"

**대화 의도 감지 (librarian 서브에이전트의 Phase E):**
- "~ 에러 해결했어" / "~ 고쳤어" / "~ 문제 있었는데"
- "~ 하기로 결정했어" / "A 대신 B로"
- "오늘 ~ 작업했어" / "~ 추가했어" / "~ 완료"
- "설치 방법은 ~" / "순서는 ~"

검색/조회 트리거는 **Step 1 (직접 검색)** 부터 시작합니다.
대화 의도 감지 트리거는 librarian 서브에이전트의 **Phase E** 로 라우팅합니다.

## 규칙

- 단순 검색은 MCP 도구 또는 CLI 직접 호출 (서브에이전트 불필요)
- 서브에이전트는 검색 실패, 문서 개선/최신화/생성 시에만 스폰
- 문서 수정/생성 전 반드시 AskUserQuestion으로 사용자 승인
- 문서 생성 시 `$CLAUDE_PLUGIN_ROOT/templates/frontmatter-guide.md`를 따름
- 최신화 검사는 기술 문서(#spec, #guide, #api, #architecture 등)에만 실행
- 목록 확인 단계: `enrich=false` 로 불필요한 메타데이터 절약
