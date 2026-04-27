---
name: add
description: 개별 문서를 템플릿 기반으로 추가하는 스킬. devlog, decision, troubleshooting 등 개발 과정에서 문서를 축적합니다 (문서 추가, doc add, devlog 추가, 개발 일지, 문서 작성, ADR, decision record)
---

# 문서 추가 (Doc Add)

개발 과정에서 문서 하나를 템플릿 기반으로 추가합니다.

## 입력

```
/doxus:add <type> "<title>"
```

| type | 카테고리 | 파일명 패턴 | 설명 |
|------|---------|------------|------|
| `devlog` | docs/devlog/ | `YYYY-MM-DD-{slug}.md` | 개발 일지 |
| `feature` | docs/devlog/ | `YYYY-MM-DD-{slug}.md` | 기능 추가 (tag: #feature) |
| `bugfix` | docs/devlog/ | `YYYY-MM-DD-{slug}.md` | 버그 수정 (tag: #bugfix) |
| `refactor` | docs/devlog/ | `YYYY-MM-DD-{slug}.md` | 리팩토링 (tag: #refactor) |
| `troubleshooting` | docs/devlog/ | `YYYY-MM-DD-{slug}.md` | 에러 해결 (tag: #troubleshooting) |
| `decision` | docs/architecture/decisions/ | `NNN-{slug}.md` | 설계 결정 (ADR) |
| `integration` | docs/integrations/ | `{slug}.md` | 외부 서비스 연동 |
| `guide` | docs/guides/ | `{slug}.md` | 가이드 문서 |
| `context` | docs/context/ | `{slug}.md` | 비즈니스 컨텍스트 |

## 실행 절차

### Step 1: MCP / CLI 감지

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` 참조.

### Step 2: 기존 문서 확인

`doxus_search` 또는 `doxus search "<title>"` 로 중복 확인.
기존 파일 있으면 AskUserQuestion: "기존 파일 업데이트 / 새 파일로 생성"

### Step 3: 문서 생성

```
Agent(
  subagent_type: "doxus:docsmith-writer",
  model: "sonnet",
  prompt: "프로젝트 경로: {cwd}. doxus 프로젝트 ID: {id}.
문서 타입: {type} / 제목: {title} / 파일 경로: {file_path}
현재 날짜: {YYYY-MM-DD} / 기존 태그 목록: [...]
템플릿 경로: $CLAUDE_PLUGIN_ROOT/templates/{template}.md
코드와 git log를 분석하여 내용 초안을 작성하세요.",
  description: "docsmith 문서 추가"
)
```

### Step 4: 후처리

재인덱싱 후 결과 보고: `MODE=mcp` → `doxus_index_project(name=<PROJECT>)` / `MODE=cli` → `doxus index`

## 규칙

- frontmatter 반드시 완전하게 채움
- devlog 파일명: `YYYY-MM-DD-{slug}.md`
- decision 파일명: `NNN-{slug}.md` (기존 번호 다음 순번)
