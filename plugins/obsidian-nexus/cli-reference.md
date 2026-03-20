# obs-nexus CLI 레퍼런스

모든 스킬과 에이전트는 이 파일을 단일 진실 소스(SSoT)로 참조합니다.

> **버전**: 0.3.7 기준. `obs-nexus --version`으로 확인.

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

### 시작 시: obs-nexus 감지 + 프로젝트 ID 확인

```bash
which obs-nexus && obs-nexus project list --format json
```

cwd 경로와 가장 가까운 항목을 프로젝트 ID로 사용합니다.

미설치 시:
```
obs-nexus가 설치되어 있지 않습니다.
  brew tap gorilla-kim/tap && brew install obs-nexus
파일시스템 기반(Glob/Grep)으로 진행할까요?
```

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
