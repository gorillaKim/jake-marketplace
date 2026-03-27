# obs-nexus CLI 레퍼런스

모든 스킬과 에이전트는 이 파일을 단일 진실 소스(SSoT)로 참조합니다.

> **버전**: 0.5.9 기준. `obs-nexus --version`으로 확인.

## 설치 확인

```bash
which obs-nexus
obs-nexus --version
```

미설치 시:
```bash
brew tap gorilla-kim/tap && brew install obs-nexus
```

## 프로젝트

```bash
# 프로젝트 목록
obs-nexus project list --format json

# 프로젝트 등록
obs-nexus project add <VAULT_PATH>

# 프로젝트 상세
obs-nexus project info <PROJECT> --format json

# 프로젝트 삭제 (인덱스만 삭제, 파일 유지)
obs-nexus project remove <PROJECT>

# 볼트 경로 변경 (이동 후 재등록)
obs-nexus project update <PROJECT> --path <NEW_PATH>
```

## 검색

```bash
# 하이브리드 검색 (기본 권장)
obs-nexus search "<query>" --project <ID> --mode hybrid --format json
obs-nexus search "<query>" --project <ID> --mode hybrid --limit 5 --format json

# 모드: keyword | vector | hybrid
```

## 랭킹

```bash
# 인기 문서 순위 (조회수 + 백링크 기반)
obs-nexus ranking --format json
obs-nexus ranking --project <ID> --limit 10 --format json
```

## 문서 조회

```bash
# 별칭으로 문서 찾기
obs-nexus doc resolve-alias "<alias>" --format json

# 문서 전체 내용
obs-nexus doc get <PROJECT> <PATH>

# 특정 섹션만 추출
obs-nexus doc section <PROJECT> <PATH> "<heading>"

# frontmatter / tags 확인
obs-nexus doc meta <PROJECT> <PATH> --format json

# 백링크 (이 문서를 참조하는 문서들)
obs-nexus doc backlinks <PROJECT> <PATH> --format json

# 포워드 링크 (이 문서가 참조하는 문서들)
obs-nexus doc links <PROJECT> <PATH> --format json

# 문서 목록 (전체 / 태그 필터)
obs-nexus doc list <PROJECT> --format json
obs-nexus doc list <PROJECT> --tags <TAG> --format json
```

> ⚠️ `doc update`, `doc move` 는 미지원. frontmatter 수정은 파일 직접 Edit, 이동은 `mv` 후 재인덱싱.

## 인덱싱

```bash
# 특정 프로젝트 인덱싱
obs-nexus index <PROJECT>

# 전체 프로젝트 인덱싱
obs-nexus index --all

# 강제 전체 재인덱싱 (content hash 무시)
obs-nexus index <PROJECT> --full
```

## 그래프 탐색

CLI와 MCP 모두 지원 (v0.5.9+).

### CLI

```bash
# 관련 문서 추천 (RRF: 링크 거리 + 태그 중복 합산)
obs-nexus graph related <PROJECT> <PATH> [--k 10] --format json

# 두 문서 간 최단 정방향 경로 (BFS, max 6 hops)
obs-nexus graph path <PROJECT> <FROM> <TO> --format json

# 멀티홉 클러스터 탐색 (앞/역방향, depth 기본 2, 최대 5)
obs-nexus graph cluster <PROJECT> <PATH> [--depth 2] --format json
```

### MCP

```
nexus_get_cluster(project, path, depth=2)
  반환: file_path, title, distance, tags, snippet

nexus_find_path(project, from, to)
  반환: 경로 배열 또는 null (경로 없음)

nexus_find_related(project, path, k=10)
  반환: 상위 k개 문서 + signals(["link", "tag"])
```

**사용 전 확인**: `obs-nexus doc links` (CLI) 또는 `nexus_get_links` (MCP)로 `"resolved": false` 비율 확인 후 `find_path` 호출

## 기타

```bash
# 볼트 변경 자동 감지 및 인덱싱
obs-nexus watch <PROJECT>

# 업데이트 확인 및 설치
obs-nexus update

# librarian 스킬/에이전트 프로젝트에 설치
obs-nexus onboard
```

## 공통 패턴

### 시작 시: MCP / CLI / 설치 안내 3단계 감지

**Step 1: MCP 연결 확인 (최우선)**
`nexus_list_projects` MCP 도구 호출 시도
→ 성공: `MODE=mcp`, 반환된 프로젝트 목록에서 현재 경로와 가장 가까운 프로젝트 ID 확인
→ 실패 (도구 없음/오류): Step 2로

**Step 2: CLI 확인 (폴백)**
`which obs-nexus && obs-nexus project list --format json`
→ 성공: `MODE=cli`, 프로젝트 ID 확인
→ 실패: Step 3으로

**Step 3: 설치 안내 (둘 다 없음)**
사용자에게 안내 후 종료:
> obs-nexus MCP 서버와 CLI가 모두 감지되지 않았습니다.
> 설치: `brew tap gorilla-kim/tap && brew install obs-nexus`
> MCP 설정: claude_desktop_config.json에 nexus MCP 서버 추가
> 설치 후 다시 실행해 주세요.

**MODE 변수 활용**:
- `MODE=mcp`: 모든 검색/조회에 MCP 도구 사용 (`nexus_search`, `nexus_get_section` 등)
- `MODE=cli`: `obs-nexus` CLI 명령어 사용

### 문서 생성/수정 후 후처리

```bash
obs-nexus index <PROJECT>
```

### frontmatter 수정 방법 (doc update 미지원)

```bash
# 1. 파일 직접 Edit (frontmatter 수정)
# 2. 재인덱싱
obs-nexus index <PROJECT>
```

## 도구 우선순위 (모든 스킬/에이전트 공통)

1. **obs-nexus CLI** — 기본. 문서 검색, 태그 조회, 메타데이터 확인
2. **Glob/Grep** — obs-nexus 미설치 시 폴백
3. **Read/Edit** — 파일 직접 접근 필요 시 (frontmatter 수정 등)
