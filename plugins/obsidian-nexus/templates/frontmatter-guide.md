# Frontmatter 가이드

문서 생성/수정 시 반드시 아래 규칙을 따릅니다.

## 필수 템플릿

```yaml
---
title: 문서 제목
aliases:
  - english-alias         # 영문 소문자, 하이픈 연결
  - 한글 별칭               # 자연어 형태
  - abbr                   # 약어/줄임말 (선택)
tags:
  - document-type-tag     # 필수: 최소 1개 (overview, guide, spec, reference, devlog)
  - domain-tag            # 기술 도메인 (architecture, database, search 등)
  - tech-stack-tag        # 구체적 기술 (선택)
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

## 필드 규칙

- **title**: 명확하고 설명적. 검색 랭킹의 제목 매칭 부스트에 사용됨.
- **aliases**: 영문/한글/약어 별칭. `obs-nexus doc resolve-alias`의 핵심 데이터.
  - 최소 영문 1개 + 한글 1개
  - 검색 실패 시 해당 검색어를 alias로 추가
- **tags**: 최대 5개, 영문 소문자, 하이픈 연결. 최소 1개 문서 유형 태그 필수.
  - 기존 태그 우선 재사용 (`obs-nexus doc list`로 확인)
  - 한글 태그 금지 → aliases에 한글 넣기
- **created**: 생성일. 한 번 설정 후 변경 금지. `YYYY-MM-DD` 형식.
- **updated**: 수정일. 내용 변경 시마다 갱신.

## 표준 태그 카테고리

| 카테고리 | 태그 |
|----------|------|
| 문서 유형 | `overview`, `guide`, `spec`, `tutorial`, `reference`, `troubleshooting`, `devlog` |
| 기술 영역 | `architecture`, `database`, `search`, `mcp`, `api`, `config`, `ui`, `logging`, `auth`, `deploy` |
| 기술 스택 | `sqlite`, `sqlite-vec`, `fts5`, `vector`, `rust`, `tauri`, `react`, `datadog`, `ollama` |
| 활동 유형 | `development`, `test`, `benchmark`, `evaluation`, `setup`, `design`, `migration` |
| 역할 대상 | `agent`, `user`, `admin` |

## 금지 사항

- 동의어 태그 중복 생성 금지 (`config` ↔ `configuration`)
- 문서 제목을 반복하는 태그 금지
- 과도하게 구체적인 태그 금지 (`nexus-search-fts5-unicode` → `search`, `fts5`로 분리)
