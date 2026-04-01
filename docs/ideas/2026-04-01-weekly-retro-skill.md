---
title: "주간 회고 스킬 (obs-nexus:retro)"
aliases:
  - weekly-retro-skill
  - 주간 회고 기능
  - retro skill idea
tags:
  - idea
  - feature
  - plugin
  - obsidian-nexus
created: "2026-04-01"
updated: "2026-04-01"
---

# 주간 회고 스킬 (`/obs-nexus:retro`)

## 개요

프로젝트별로 `decision`, `devlog`, `idea` 태그가 달린 문서들을 날짜 범위로 검색하고, 내용을 딥 요약하여 주간 회고 문서를 자동 생성하는 스킬. 멀티 프로젝트 병렬 처리를 지원한다.

### 배경

- `nexus_search`에 날짜 범위 + 태그 필터 검색이 추가됨 (`date_from`, `date_to`, `tags`)
- 기존 `session-devlog`는 단일 세션 단위 → 주 단위 종합 회고 기능이 없음
- 여러 프로젝트를 동시에 운영할 때 크로스 프로젝트 인사이트가 필요함

## 스킬 인터페이스

```
/obs-nexus:retro [--projects "A,B,C"] [--tags "decision,devlog,idea,bug"] [--model sonnet]
```

| 인자 | 기본값 | 설명 |
|------|--------|------|
| `--projects` | (사용자 선택) | 회고 대상 프로젝트 (복수 가능) |
| `--tags` | `decision,devlog,idea` | 검색할 태그 목록 (확장 가능) |
| `--model` | `sonnet` (추천) | gatherer/writer 에이전트 모델 |

## 파이프라인 설계

### 에이전트 구성

| 에이전트 | 타입 | 모델 | 역할 |
|----------|------|------|------|
| `retro-coordinator` | Team Agent | sonnet | 사용자 인터뷰, 파라미터 확정, 병렬 조율 |
| `retro-gatherer` | Sub Agent | 사용자 선택 | 프로젝트별 검색 + 딥 요약 |
| `retro-writer` | Sub Agent | 사용자 선택 | 회고 문서 + 종합 문서 생성 |

### 흐름

```
사용자: /obs-nexus:retro

┌─────────────────────────────────────────────────────────────┐
│  STEP 1. retro-coordinator (Team Agent, sonnet)             │
│                                                             │
│  ① nexus_list_projects → 목록 + CWD 기반 가장 가까운 추천   │
│  ② AskUser: 프로젝트 선택 (복수 가능)                       │
│  ③-a 선택 프로젝트별 nexus_search(                          │
│       tags: ["weekly-retro"],                               │
│       sort_by: "date_desc", date_field: "created_at", limit:1│
│     ) → 최근 회고 문서 탐지                                  │
│  ③-b nexus_get_metadata(path: "{found_doc}") →              │
│       frontmatter JSON 파싱 → period.to 추출                 │
│  ③-c nexus_search(tags: ["weekly-retro", "{W번호}"],        │
│       tag_match_all: true, limit: 1) → 멱등성 체크           │
│     - 결과 있음 → "W** 회고가 이미 존재합니다. 덮어쓸까요?"  │
│       → Yes: 덮어쓰기 / No: 스킬 종료                       │
│  ④ AskUser: 날짜 범위 옵션 제시                              │
│     - Option 1 (기본): {period.to + 1일} ~ 오늘              │
│     - Option 2~N: 최근 4주 ISO 8601 주차 범위 목록           │
│     - 직접 입력 항상 포함                                    │
│     - 첫 회고 → 최근 7일 제안 + 직접 입력 가능               │
│  ⑤ AskUser: 모델 선택 (기본 sonnet 추천)                    │
│  ⑥ 추가 태그? (기본: decision, devlog, idea)                │
│  ⑦ 멀티 프로젝트 → 종합 문서 저장할 프로젝트 선택           │
└──────────────┬──────────────────────────────────────────────┘
               │
       ┌───────┼────────┐       ← Agent 도구로 병렬 호출
       ↓       ↓        ↓
    ┌──────┐┌──────┐┌──────┐
    │Proj A││Proj B││Proj C│   retro-gatherer (Sub, 선택 모델)
    │      ││      ││      │
    │ 태그별 nexus_search   │   ❶ 태그별 검색 (date_from/to)
    │ nexus_get_section     │   ❷ Deep 읽기 (섹션 추출)
    │ 요약 + JSON 저장      │   ❸ .omc/retro/{proj}.json
    └──┬───┘└──┬───┘└──┬───┘
       └───────┼───────┘
               ↓
    ┌───────────────────────────────────────────────┐
    │  retro-writer (Sub Agent, 선택 모델)           │
    │                                               │
    │  ❶ 중간결과 JSON 로드                          │
    │  ❷ 프로젝트별 회고문서 생성                     │
    │     → {vault}/retro/2026/W14.md               │
    │  ❸ 멀티 프로젝트면 종합 문서 생성               │
    │     → {선택 vault}/retro/2026/W14-summary.md  │
    │  ❹ 액션 아이템 추출 → coordinator에 반환        │
    └──────────────┬────────────────────────────────┘
                   ↓
    ┌───────────────────────────────────────────────┐
    │  retro-coordinator (계속)                      │
    │                                               │
    │  ❺ 액션 아이템 표시 → AskUser:                 │
    │     "TODO 문서로 생성할까요?"                    │
    │     → Yes: {vault}/retro/2026/W14-actions.md  │
    │     → No: 회고 문서 내 체크리스트로만 유지       │
    └───────────────────────────────────────────────┘
```

## 날짜 범위 탐지 로직

```
# Step 1: 최근 회고 문서 탐지 (created_at 기준 정렬 — 편집해도 순서 불변)
nexus_search(
  tags: ["weekly-retro"],
  project: "A",
  sort_by: "date_desc",
  date_field: "created_at",
  limit: 1
)

# Step 2: 탐지된 문서에서 period.to 읽기
nexus_get_metadata(project: "A", path: "{found_doc.file_path}")
→ frontmatter JSON 파싱 → period.to 추출
  (period.to 없으면 created_at으로 폴백)

# Step 3: 날짜 범위 옵션 제시
→ 결과 있음:
    Option 1 (기본): {period.to + 1일} ~ 오늘  ← 결정론적, edit-proof
    Option 2~N: 최근 4주 ISO 8601 주차 범위 자동 생성
              예) "3/25~3/31 (W13)", "3/18~3/24 (W12)" ...
    직접 입력 항상 포함
    → AskUser: "어떤 범위로 회고를 생성할까요?"
→ 결과 없음 (첫 회고): 최근 7일 제안 + 직접 입력 가능
```

## 중간결과 JSON 스키마 (gatherer → writer)

```json
{
  "project": "obsidian-nexus",
  "vault_path": "/Users/jake/vaults/obsidian-nexus",
  "period": { "from": "2026-03-25", "to": "2026-03-31" },
  "categories": {
    "decision": [
      {
        "path": "docs/decisions/search-engine.md",
        "title": "검색 엔진 선택",
        "date": "2026-03-27",
        "summary": "FTS5 + sqlite-vec 하이브리드로 결정...",
        "key_points": ["포인트1", "포인트2"],
        "related_docs": ["[[아키텍처]]", "[[검색 설계]]"]
      }
    ],
    "devlog": [],
    "idea": []
  },
  "stats": {
    "total_docs": 12,
    "by_tag": { "decision": 3, "devlog": 7, "idea": 2 }
  }
}
```

## 출력 문서 구조

### 프로젝트별 회고 (`{vault}/retro/2026/W14.md`)

```markdown
---
title: "주간 회고 2026-W14"
aliases: [weekly-retro-W14, 주간회고-W14]
tags: [weekly-retro, "2026-W14"]
created: 2026-04-01
period:
  from: 2026-03-25
  to: 2026-03-31
project: obsidian-nexus
---

# 주간 회고 — 2026-W14 (3/25 ~ 3/31)

## 📊 이번 주 요약
> decision 3건 / devlog 7건 / idea 2건

## 🔨 주요 결정사항 (Decision)
### [[검색 엔진 선택]]
- 요약 내용...
- **핵심 근거**: ...
- **영향 범위**: ...

## 📝 개발 로그 (Devlog)
### [[인덱서 성능 개선]]
- 요약 내용...

## 💡 아이디어 (Idea)
### [[캐시 레이어 도입]]
- 요약 내용...

## ✅ 제안 액션 아이템
- [ ] 검색 엔진 마이그레이션 계획 수립
- [ ] 캐시 레이어 PoC 착수 검토
```

### 종합 문서 (멀티 프로젝트, `{선택 vault}/retro/2026/W14-summary.md`)

```markdown
---
title: "주간 종합 회고 2026-W14"
tags: [weekly-retro, weekly-retro-summary, "2026-W14"]
projects: [obsidian-nexus, jake-marketplace]
period:
  from: 2026-03-25
  to: 2026-03-31
---

# 주간 종합 회고 — 2026-W14

## 프로젝트별 요약
| 프로젝트 | Decision | Devlog | Idea | 핵심 사항 |
|----------|----------|--------|------|-----------|
| obsidian-nexus | 3 | 7 | 2 | 검색 엔진 전환 결정 |
| jake-marketplace | 1 | 4 | 1 | 플러그인 구조 개편 |

## 크로스 프로젝트 인사이트
- obsidian-nexus의 검색 API 변경이 jake-marketplace 플러그인에 영향
- ...

## ✅ 통합 액션 아이템
- [ ] ...
```

### 액션 TODO 문서 (선택, `{vault}/retro/2026/W14-actions.md`)

```markdown
---
title: "액션 아이템 2026-W14"
aliases: [actions-W14, 액션아이템-W14]
tags: [weekly-retro, action-items, "2026-W14"]
created: 2026-04-01
period:
  from: 2026-03-25
  to: 2026-03-31
project: obsidian-nexus
source: "[[retro/2026/W14]]"
---

# 액션 아이템 — 2026-W14

> 📋 [[retro/2026/W14|주간 회고 2026-W14]]에서 도출

## 🔴 높은 우선순위
- [ ] 검색 엔진 마이그레이션 계획 수립
  - 근거: [[검색 엔진 선택]] decision에서 확정됨
  - 기한 제안: W15 내
- [ ] API 인증 문서 업데이트
  - 근거: [[API 인증 방식]] 변경으로 기존 문서 outdated
  - 기한 제안: W15 내

## 🟡 검토 필요
- [ ] 캐시 레이어 PoC 착수 여부 결정
  - 근거: [[캐시 레이어 도입]] 아이디어에서 도출
  - 판단 필요: 리소스 여유 확인 후

## 🟢 낮은 우선순위
- [ ] 테스트 커버리지 확대
  - 근거: [[인덱서 성능 개선]] devlog에서 커버리지 부족 언급

## 메모
- 지난 주 액션 아이템 중 미완료 항목: (해당 시 자동 이월)
```

## 플러그인 내 파일 구조

```
plugins/obsidian-nexus/
├── skills/
│   └── retro/
│       └── SKILL.md                  ← 스킬 정의
├── agents/
│   ├── retro-coordinator.md          ← Team Agent
│   ├── retro-gatherer.md             ← Sub Agent (검색+요약)
│   └── retro-writer.md               ← Sub Agent (문서 생성)
├── templates/
│   ├── retro.md                      ← 프로젝트별 회고 템플릿
│   ├── retro-summary.md              ← 종합 회고 템플릿
│   └── retro-actions.md              ← 액션 TODO 템플릿
```

## 핵심 의존성

- **nexus_search**: 날짜 범위 + 태그 필터 검색, 최근 회고 탐지 (핵심)
- **nexus_get_metadata**: 회고 문서 frontmatter에서 `period.to` 추출 (날짜 탐지)
- **nexus_get_section**: 딥 요약을 위한 섹션 추출 (gatherer)
- **nexus_list_projects**: 프로젝트 목록 + CWD 기반 추천
- **Agent 도구**: 서브에이전트 병렬 호출 (프로젝트별 gatherer)

## 구현 순서 (제안)

1. 템플릿 3종 작성 (`retro.md`, `retro-summary.md`, `retro-actions.md`)
2. `retro-gatherer` 서브에이전트 (검색 + 요약 로직)
3. `retro-writer` 서브에이전트 (문서 생성 로직)
4. `retro-coordinator` 팀에이전트 (인터뷰 + 조율)
5. `SKILL.md` 스킬 정의
6. 기존 스킬과 통합 테스트

## 관련 문서

- [[plugins/obsidian-nexus/skills/session-devlog/SKILL]] — 단일 세션 devlog 생성 (참고 패턴)
- [[plugins/obsidian-nexus/agents/docsmith-analyzer]] — 프로젝트 분석 에이전트 (참고 패턴)
- [[plugins/obsidian-nexus/agents/docsmith-writer]] — 문서 생성 에이전트 (참고 패턴)
- [[plugins/obsidian-nexus/templates/devlog]] — devlog 템플릿 (참고)
