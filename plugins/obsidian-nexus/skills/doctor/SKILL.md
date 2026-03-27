---
name: doctor
description: docs/ 폴더의 문서 상태를 진단하고 개선을 제안하는 스킬. frontmatter 완전성, 오래된 문서, 코드-문서 불일치, 태그 일관성을 점검합니다 (문서 진단, doc doctor, 문서 점검, 문서 건강, docs 상태, 문서 체크)
---

# 문서 상태 진단 (Doc Doctor)

docs/ 폴더의 건강 상태를 점검하고 개선을 제안합니다.

## 입력

```
/obs-nexus:doctor
/obs-nexus:doctor --fix    # 자동 수정 모드
```

## 점검 항목

### 1. frontmatter 완전성

모든 docs/ 내 마크다운 파일의 frontmatter를 점검합니다:

| 필드 | 필수 | 점검 내용 |
|------|------|----------|
| `title` | 필수 | 누락 여부 |
| `aliases` | 필수 | 최소 영문 1개 + 한글 1개 |
| `tags` | 필수 | 최소 1개 문서 유형 태그, 영문 소문자 하이픈 |
| `created` | 필수 | YYYY-MM-DD 형식 |
| `updated` | 필수 | YYYY-MM-DD 형식, created보다 이전이면 경고 |

### 2. 오래된 문서

- `updated`가 **3개월 이상** 지난 기술 문서 (tags에 spec, guide, api, architecture 포함)
- 오래된 문서 목록과 마지막 수정일을 보고

### 3. 코드-문서 불일치

- `architecture/module-map.md`에 기술된 모듈과 실제 디렉토리 구조 비교
- `overview/tech-stack.md`의 기술 스택과 실제 의존성 파일 비교
- 새로 추가된 모듈이 문서에 반영되지 않은 경우 감지

### 4. 필수 문서 누락

필수 5문서의 존재 여부 확인:
- `docs/overview/project-summary.md`
- `docs/overview/tech-stack.md`
- `docs/overview/glossary.md`
- `docs/architecture/module-map.md`
- `docs/guides/getting-started.md`

### 5. 태그 일관성

obs-nexus 연동 시 `obs-nexus doc list <PROJECT> --format json`으로 확인:
- 동의어 태그 중복 (`config` ↔ `configuration`)
- 미사용 태그 (어떤 문서에도 없는 태그)
- 태그 없는 문서

### 6. 깨진 링크 (Broken Links)

- **MCP 모드**: 각 문서에 `nexus_get_links` 호출 → `"resolved": false`인 링크 수집
- **CLI 모드**: `obs-nexus doc links <PROJECT> <PATH> --format json` 후 `resolved: false` 필터
- 미해결 위키링크 (`[[표시 이름]]` 형식)는 `nexus_find_path` 탐색에서 무시됨
- 수정 방법: `[[표시 이름]]` → `[[architecture/database-schema]]` 처럼 **파일 경로 기반**으로 변경

## 실행 절차

→ CLI 명령어: `$CLAUDE_PLUGIN_ROOT/cli-reference.md` 참조

### Step 1: MCP / CLI 감지

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` — "공통 패턴 > MCP / CLI / 설치 안내 3단계 감지" 절차를 따릅니다.

### Step 2: 문서 스캔

**MODE=mcp:** `nexus_search(enrich=false)`, `nexus_get_metadata` 사용 (목록 확인 시 enrich=false로 토큰 절약)
**MODE=cli:** `obs-nexus doc list`, `obs-nexus doc meta` 사용

**미설치 시:** Glob으로 `docs/**/*.md` 스캔, Grep으로 frontmatter 파싱

### Step 3: 진단 리포트 생성

Health Score 계산:
- 기본 100점에서 감점
- frontmatter 필드 누락: 항목당 -5점
- 오래된 문서 (3개월+): 문서당 -3점
- 코드-문서 불일치: 항목당 -10점
- 필수 문서 누락: 문서당 -8점
- 동의어 태그 중복: 쌍당 -2점
- 깨진 링크 (resolved: false): 링크당 -1점

```
📋 문서 상태 진단 결과

🏥 문서 건강도: 72 / 100
   ████████████████████░░░░░░░░░░  (목표: 90점 이상)

✅ 정상: 8개 문서
⚠️ 경고: 3개 문서
❌ 문제: 2개 문서

--- frontmatter 문제 ---
❌ docs/architecture/module-map.md
   - aliases 누락 (한글 별칭 없음)
   - updated가 created보다 이전

⚠️ docs/guides/getting-started.md
   - tags에 문서 유형 태그 없음

--- 오래된 문서 ---
⚠️ docs/overview/tech-stack.md
   - 마지막 수정: 2025-12-15 (3개월 전)

--- 코드-문서 불일치 ---
❌ docs/architecture/module-map.md
   - crates/agent/ 모듈이 추가되었으나 문서에 미반영

--- 필수 문서 누락 ---
⚠️ docs/overview/glossary.md — 없음

--- 태그 일관성 ---
⚠️ 동의어 태그 발견: "config" (2개 문서) ↔ "configuration" (1개 문서)

--- 깨진 링크 ---
⚠️ docs/overview/project-overview.md
   - [[04-데이터베이스-스키마]] → resolve 실패
   - [[03-MCP-도구-레퍼런스]] → resolve 실패
   수정 방법: [[표시 이름]] → [[architecture/database-schema]] 형식으로 변경

자동 수정 가능한 항목: 3개
```

진단 후 AskUserQuestion으로 확인:

```
AskUserQuestion(
  question: "자동 수정 가능한 항목이 {N}개 있습니다. 진행할까요?\n\n{항목 목록}",
  options: ["자동 수정 진행", "수동으로 처리"]
)
```

### Step 4: 자동 수정 (--fix 모드)

`--fix` 인자가 있으면 자동 수정 가능한 항목을 처리합니다:

1. **frontmatter 보완**: 누락된 aliases, tags 추가
2. **updated 날짜 수정**: 잘못된 날짜 보정
3. **동의어 태그 통합**: AskUserQuestion으로 선택
   ```
   AskUserQuestion(
     question: "동의어 태그를 하나로 통합합니다. 어떤 태그로 통일할까요?\n\n{tag_a} ({N}개 문서) ↔ {tag_b} ({M}개 문서)",
     options: ["{tag_a}로 통합", "{tag_b}로 통합", "건너뜀"]
   )
   ```

수정 후:
```bash
obs-nexus index <PROJECT>  # 재인덱싱
```

자동 수정 불가 항목 (사용자 개입 필요):
- 코드-문서 불일치 → `/obs-nexus:add` 또는 수동 수정 안내
- 필수 문서 누락 → `/obs-nexus:onboard` 안내
- 오래된 문서 → 수동 검토 권장
- 깨진 링크 → 위키링크를 파일 경로 기반으로 수동 수정 안내
  (예: `[[04-데이터베이스-스키마]]` → `[[architecture/database-schema]]`)

## 규칙

- 진단만 하고 자동 수정하지 않음 (--fix 없으면)
- 자동 수정 시에도 내용 변경은 하지 않음 (frontmatter만 수정)
- 문서 내용의 정확성 검증은 범위 밖 (구조적 점검만)
