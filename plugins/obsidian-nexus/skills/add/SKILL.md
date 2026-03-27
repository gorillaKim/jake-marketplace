---
name: add
description: 개별 문서를 템플릿 기반으로 추가하는 스킬. devlog, decision, troubleshooting 등 개발 과정에서 문서를 축적합니다 (문서 추가, doc add, devlog 추가, 개발 일지, 문서 작성, ADR, decision record)
---

# 문서 추가 (Doc Add)

개발 과정에서 문서 하나를 템플릿 기반으로 추가합니다.
주로 devlog, troubleshooting, decision 등 상시 축적 문서에 사용합니다.

## 입력

```
/obs-nexus:add <type> "<title>"
```

| type | 카테고리 | 파일명 패턴 | 설명 |
|------|---------|------------|------|
| `devlog` | docs/devlog/ | `YYYY-MM-DD-{slug}.md` | 개발 일지 |
| `feature` | docs/devlog/ | `YYYY-MM-DD-{slug}.md` | 기능 추가 기록 (tag: #feature) |
| `bugfix` | docs/devlog/ | `YYYY-MM-DD-{slug}.md` | 버그 수정 기록 (tag: #bugfix) |
| `refactor` | docs/devlog/ | `YYYY-MM-DD-{slug}.md` | 리팩토링 기록 (tag: #refactor) |
| `troubleshooting` | docs/devlog/ | `YYYY-MM-DD-{slug}.md` | 에러 해결 기록 (tag: #troubleshooting) |
| `decision` | docs/architecture/decisions/ | `NNN-{slug}.md` | 설계 결정 (ADR) |
| `integration` | docs/integrations/ | `{slug}.md` | 외부 서비스 연동 |
| `guide` | docs/guides/ | `{slug}.md` | 가이드 문서 |
| `context` | docs/context/ | `{slug}.md` | 비즈니스 컨텍스트 |

예시:
```
/obs-nexus:add devlog "검색 리랭킹 개선"
/obs-nexus:add troubleshooting "sqlite-vec 빌드 에러"
/obs-nexus:add decision "임베딩 모델 선택"
/obs-nexus:add integration "Ollama API"
```

## 실행 절차

### Step 1: MCP / CLI 감지 및 프로젝트 ID 확인

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` — "공통 패턴 > MCP / CLI / 설치 안내 3단계 감지" 절차를 따릅니다.

### Step 2: 기존 문서 확인

obs-nexus 설치 시: `obs-nexus search "<title>" --project <ID> --mode hybrid --format json`

미설치 시: Glob으로 docs/ 스캔하여 유사 파일명 확인

**기존 파일이 있으면**: AskUserQuestion으로 확인
```
AskUserQuestion(
  question: '"{파일경로}"가 이미 존재합니다. 어떻게 할까요?',
  options: ["기존 파일 업데이트", "새 파일로 생성"]
)
```

### Step 3: 문서 생성

docsmith-writer를 스폰하여 문서를 생성합니다:

```
Agent(
  subagent_type: "obs-nexus:docsmith-writer",
  model: "sonnet",
  prompt: "프로젝트 경로: {cwd}. nexus 프로젝트 ID: {id}.
문서 타입: {type}
제목: {title}
카테고리: {category}
파일 경로: {file_path}
현재 날짜: {YYYY-MM-DD}
기존 태그 목록: [...]
템플릿 경로: $CLAUDE_PLUGIN_ROOT/templates/{template}.md

코드와 git log를 분석하여 내용 초안을 작성하세요.
기존 파일이 있으면 update 모드로 내용을 병합하세요.",
  description: "docsmith 문서 추가"
)
```

### Step 4: 후처리

1. obs-nexus 연동 시: `obs-nexus index <PROJECT>`로 재인덱싱
2. 결과 보고:
```
문서 생성 완료!
  docs/devlog/2026-03-20-search-reranking.md ✅
  tags: [devlog, feature, search]
  aliases: [search-reranking, 검색 리랭킹]
```

## 업데이트 모드

기존 파일이 있고 사용자가 업데이트를 선택한 경우:
1. 기존 내용을 Read로 읽음
2. `<!-- docsmith: auto-generated -->` 마커가 있으면 → 재생성 가능
3. 마커가 없으면 → 내용 추가(append)만, 기존 내용 수정 금지
4. `updated` 날짜를 오늘로 갱신

## 규칙

- frontmatter를 반드시 완전하게 채움 (tags, aliases, created 필수)
- devlog 파일명은 `YYYY-MM-DD-{slug}.md` 형식
- decision(ADR) 파일명은 `NNN-{slug}.md` (기존 번호 다음 순번)
- nexus 관련 문서 검색으로 `## 관련 문서` 섹션 자동 채움
- 아키텍처 관련 문서에는 Mermaid 다이어그램 활용
