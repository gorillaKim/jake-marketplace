---
name: doctor
description: docs/ 폴더의 문서 상태를 진단하고 개선을 제안하는 스킬. frontmatter 완전성, 오래된 문서, 코드-문서 불일치, 태그 일관성을 점검합니다 (문서 진단, doc doctor, 문서 점검, 문서 건강, docs 상태, 문서 체크)
---

# 문서 상태 진단 (Doc Doctor)

docs/ 폴더의 건강 상태를 점검하고 개선을 제안합니다.

## 입력

```
/doxus:doctor
/doxus:doctor --fix
```

## 점검 항목

### 1. frontmatter 완전성
- `title`, `aliases` (영문+한글 최소 1개씩), `tags` (최소 1개), `created`, `updated` 필수

### 2. 오래된 문서
- `updated`가 3개월 이상 지난 기술 문서 (spec, guide, api, architecture 태그)

### 3. 코드-문서 불일치
- module-map.md의 모듈 vs 실제 디렉토리 구조
- tech-stack.md vs 실제 의존성 파일

### 4. 필수 문서 누락
- overview/project-summary.md, tech-stack.md, glossary.md
- architecture/module-map.md, guides/getting-started.md

### 5. 태그 일관성
- 동의어 태그 중복, 미사용 태그, 태그 없는 문서

### 6. 깨진 링크
- `doxus_get_links` → `"resolved": false`인 링크 수집
- 수정 방법: `[[표시 이름]]` → `[[architecture/database-schema]]` 파일 경로 기반으로 변경

## 실행 절차

### Step 1: MCP / CLI 감지

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` 참조.

### Step 2: 문서 스캔

**MODE=mcp:** `doxus_search(enrich=false)`, `doxus_get_metadata` 활용
**MODE=cli:** `Glob docs/**/*.md` + `Read` 로 frontmatter 직접 파싱 (`doxus doc` 서브커맨드 없음)

### Step 3: 진단 리포트 생성 + Health Score

기본 100점, 항목별 감점:
- frontmatter 필드 누락: -5점/항목
- 오래된 문서: -3점/문서
- 코드-문서 불일치: -10점/항목
- 필수 문서 누락: -8점/문서
- 동의어 태그: -2점/쌍
- 깨진 링크: -1점/링크

### Step 4: 자동 수정 (--fix 모드)

1. frontmatter 보완 (누락 aliases, tags 추가)
2. updated 날짜 수정
3. 동의어 태그 통합 (AskUserQuestion으로 선택)

수정 후 재인덱싱: `MODE=mcp` → `doxus_index_project(name=<PROJECT>)` / `MODE=cli` → `doxus index`

자동 수정 불가 항목: 코드-문서 불일치, 필수 문서 누락, 오래된 문서, 깨진 링크는 수동 안내.

## 규칙

- 진단만 하고 자동 수정하지 않음 (--fix 없으면)
- 자동 수정 시에도 내용 변경은 하지 않음 (frontmatter만 수정)
