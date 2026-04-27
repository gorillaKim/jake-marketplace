# doxus CLI 레퍼런스

모든 스킬과 에이전트는 이 파일을 단일 진실 소스(SSoT)로 참조합니다.

> **버전**: `doxus --version`으로 확인.

## MCP 도구 (최우선)

MCP 서버가 연결되어 있으면 CLI보다 MCP 도구를 먼저 사용합니다:

| 도구 | 설명 | 사용 시점 |
|------|------|---------|
| `doxus_list_projects` | 프로젝트 목록 조회 | 항상 |
| `doxus_search` | 검색 (기본 hybrid, `mode` 인자로 fts/vector 전환 가능) | 문서 탐색 |
| `doxus_get_document` | 문서 전체 내용 | 전체 읽기 |
| `doxus_get_section` | 특정 섹션 추출 (토큰 절약) | 섹션만 필요 시 |
| `doxus_get_backlinks` | 역방향 링크 탐색 | 관련 문서 탐색 |
| `doxus_get_links` | 정방향 링크 탐색 | 관련 문서 탐색 |
| `doxus_get_metadata` | 태그/frontmatter 조회 | 메타 확인 |
| `doxus_list_documents` | 프로젝트 문서 목록 | 전수 조사 |
| `doxus_resolve_alias` | 별칭으로 문서 찾기 | alias 검색 |
| `doxus_index_project` | 특정 프로젝트 재인덱싱 | 문서 생성 후 |
| `doxus_get_toc` | 목차 조회 | 섹션 탐색 전 |
| `doxus_get_cluster` | 멀티홉 클러스터 탐색 (depth 기본 2) | 관계 탐색 |
| `doxus_find_path` | 두 문서 간 최단 경로 | 경로 탐색 |
| `doxus_agent_summary` | 프로젝트 전체 상태/태그 요약 | 태그 분포 파악 |
| `doxus_create_document` | 문서 생성 | 문서 작성 |
| `doxus_get_freshness_report` | 문서 신선도 리포트 | doctor 진단 |
| `doxus_get_documents` | 복수 문서 일괄 조회 | 벌크 읽기 |
| `doxus_inspect_document` | 문서 상세 분석 | 디버깅 |
| `doxus_explain_search` | 검색 결과 설명 | 검색 품질 확인 |
| `doxus_status` | 서버 상태 확인 | 연결 확인 |
| `doxus_diagnose` | 프로젝트 문제 진단 | doctor 진단 |
| `doxus_get_ranking` | 문서 랭킹 조회 | 중요도 파악 |
| `doxus_onboard` | 프로젝트 온보딩 | 초기 설정 |
| `doxus_help` | 도구 사용법 조회 | 디버깅 |
| `doxus_add_project` | 프로젝트 추가 (MCP) | 프로젝트 등록 |
| `doxus_sync_project` | 프로젝트 동기화 | 설정 동기화 |

> **`doxus_search` 인자**: `query`, `project`, `mode` (hybrid/fts/vector, 기본 hybrid), `limit`, `offset`
> **참고**: `find_related`는 nexus 전용 기능으로 doxus에서는 미지원 — `doxus_get_cluster` / `doxus_get_backlinks`로 대체

## CLI 명령어 (MCP 미연결 시 폴백)

### 프로젝트

```bash
doxus project list
doxus project add <NAME> <VAULT_PATH>    # name과 path 둘 다 필수
doxus project remove <NAME>
doxus project enable <NAME>
doxus project disable <NAME>
```

### 검색

```bash
doxus search "<query>"
doxus search "<query>" --project <NAME>
doxus search "<query>" --project <NAME> --limit 5
# 검색 모드 선택은 MCP의 doxus_search(mode=...) 에서만 가능
# --format, --mode 플래그 없음
```

### 인덱싱

```bash
doxus index    # 활성화된 모든 프로젝트 인덱싱 (인자/플래그 없음)
# 특정 프로젝트만 인덱싱: MCP의 doxus_index_project(name=<NAME>) 사용
```

### 기타

```bash
doxus status
doxus plugin ...
doxus workspace ...
doxus graph ...
```

## ⚠️ 문서 조회는 MCP 전용

아래 기능은 **CLI 동등 명령이 없습니다** — MCP 모드에서만 사용 가능:

- 문서 내용 조회: `doxus_get_document`, `doxus_get_section`
- 문서 목록: `doxus_list_documents`
- 메타데이터: `doxus_get_metadata`
- 링크 탐색: `doxus_get_backlinks`, `doxus_get_links`
- Alias 조회: `doxus_resolve_alias`
- 그래프: `doxus_get_cluster`, `doxus_find_path`

**CLI 폴백 (MCP 미연결 시)**: `Glob docs/**/*.md` + `Read` + `Grep`으로 직접 vault 탐색.

## 공통 패턴

### 시작 시: MCP / CLI / 설치 안내 3단계 감지

**Step 1: MCP 연결 확인 (최우선)**
`doxus_list_projects` MCP 도구 호출 시도
→ 성공: `MODE=mcp`, 현재 경로와 가장 가까운 프로젝트 ID 확인
→ 실패: Step 2로

**Step 2: CLI 확인 (폴백)**
`which doxus && doxus project list`
→ 성공: `MODE=cli`
→ 실패: Step 3으로

**Step 3: 설치 안내 (둘 다 없음)**
> doxus MCP 서버와 CLI가 모두 감지되지 않았습니다.
> 팀 슬랙 **#doxus** 채널에서 **jake**에게 설치를 요청해 주세요.
> MCP 설정은 jake가 안내해 드립니다.

**MODE 변수 활용**:
- `MODE=mcp`: MCP 도구 사용
- `MODE=cli`: `doxus` CLI 사용 (문서 조회 기능 제한)

### 문서 생성/수정 후 후처리

```
MODE=mcp → doxus_index_project(name=<PROJECT_NAME>)
MODE=cli → doxus index
```

## 도구 우선순위 (모든 스킬/에이전트 공통)

1. **doxus MCP 도구** — 기본 (문서 조회 포함 전 기능)
2. **doxus CLI** — MCP 미연결 시 폴백 (검색/인덱싱만 가능)
3. **Glob/Grep/Read** — doxus 미설치 시 최후 폴백
