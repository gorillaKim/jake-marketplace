# Frontmatter 가이드

## 필수 템플릿

```yaml
---
title: 문서 제목
aliases:
  - english-alias
  - 한글 별칭
  - abbr
tags:
  - document-type-tag  # 필수: overview, guide, spec, reference, devlog
  - domain-tag
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

## 필드 규칙

- **aliases**: 최소 영문 1개 + 한글 1개. 검색 실패 시 해당 검색어를 alias로 추가.
- **tags**: 최대 5개, 영문 소문자, 하이픈 연결. 최소 1개 문서 유형 태그 필수. 한글 태그 금지.
- **created**: 생성일, 한 번 설정 후 변경 금지.
- **updated**: 내용 변경 시마다 갱신.

## 표준 태그 카테고리

| 카테고리 | 태그 |
|----------|------|
| 문서 유형 | `overview`, `guide`, `spec`, `tutorial`, `reference`, `troubleshooting`, `devlog` |
| 기술 영역 | `architecture`, `database`, `search`, `mcp`, `api`, `config`, `ui`, `auth`, `deploy` |
| 활동 유형 | `development`, `test`, `benchmark`, `setup`, `design`, `migration` |

## 금지 사항

- 동의어 태그 중복 생성 금지
- 문서 제목을 반복하는 태그 금지
- 과도하게 구체적인 태그 금지
