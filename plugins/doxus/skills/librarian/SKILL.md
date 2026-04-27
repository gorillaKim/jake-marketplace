---
name: librarian
description: doxus 기반 문서 탐색 사서. 정보 검색, 문서 최신화, 발견성 개선, 문서 생성 지원 (사서, librarian, 문서 찾기, 정보 탐색, 문서 검색, 문서 최신화, 문서 업데이트, 문서 있어, 문서 어디, docs, 매뉴얼, 가이드, 참고 문서, 정보 어디, 기록이 있, 문서 생성, 문서 작성)
---

# 사서 (Librarian)

doxus MCP/CLI를 활용한 문서 탐색 및 관리 스킬.
**2단계 구조**: 단순 검색은 직접, 복잡한 작업은 서브에이전트로 처리합니다.

## 입력

```
/doxus:librarian 검색 시스템 아키텍처
/doxus:librarian --team
/doxus:librarian 문서 최신화해줘
```

## 실행 절차

### Step 0: MCP / CLI 감지

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` 참조.

### Step 1: 직접 검색

**탐색 전략 우선순위**:
1. 특정 문서 경로를 알고 있다면 → `doxus_get_cluster(project, path, depth=2)` 먼저
2. 키워드로 문서를 특정하기 어렵다면 → `doxus_search` 폴백

**MODE=mcp** (키워드 검색 → graph 확장, 2단계 필수):
1. `doxus_search(query, project, mode="hybrid", limit=5)`
2. 상위 문서 경로로 `doxus_get_cluster(project, path, depth=2)` 확장
3. 필요 시 `doxus_get_toc(path)` → `doxus_get_section(path, heading_path)`

**MODE=cli**:
```bash
doxus search "<질의>" --project <NAME> --limit 5
# section 추출은 MCP의 doxus_get_section만 가능 (CLI 동등 명령 없음)
```

결과를 직접 전달 → **완료**

### Step 2: 서브에이전트 스폰 (검색 실패 또는 문서 관리 필요 시)

```
Agent(
  subagent_type: "doxus:librarian",
  model: "haiku",
  prompt: "검색 질의: '{질의}'. doxus 프로젝트 ID: {id}. Phase A부터 심층 검색 및 발견성 개선을 진행하세요.",
  description: "사서 심층 검색"
)
```

### Step 3: 팀원 모드 (--team)

```
TeamCreate(name: "librarian")
멤버: librarian sub-agent × 1 (doxus:librarian, haiku)
SendMessage → Phase A 심층 검색 시작
종료: 에이전트 응답 수신 후 결과 사용자에게 전달
```

## 규칙

- 단순 검색은 직접 처리 (서브에이전트 불필요)
- 서브에이전트는 검색 실패, 문서 개선/최신화/생성 시에만 스폰
- 목록 확인 시 `enrich=false`로 토큰 절약
