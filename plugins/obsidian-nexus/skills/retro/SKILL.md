---
name: retro
description: 프로젝트별 decision/devlog/idea 문서를 날짜 범위로 수집하여 주간 회고 문서를 자동 생성하는 스킬. 멀티 프로젝트 병렬 처리 지원 (주간 회고, retro, weekly retro, 회고 생성, 주간 정리)
---

# 주간 회고 스킬 (`/obs-nexus:retro`)

프로젝트별 `decision`, `devlog`, `idea` 태그 문서를 날짜 범위로 검색하고,
내용을 딥 요약하여 주간 회고 문서를 자동 생성합니다.
멀티 프로젝트 병렬 처리와 크로스 프로젝트 종합 문서를 지원합니다.

## 인터페이스

```
/obs-nexus:retro
/obs-nexus:retro --projects "A,B,C"
/obs-nexus:retro --tags "decision,devlog,idea,bug"
/obs-nexus:retro --model haiku
```

| 인자 | 기본값 | 설명 |
|------|--------|------|
| `--projects` | (인터뷰에서 선택) | 회고 대상 프로젝트, 복수 가능 |
| `--tags` | `decision,devlog,idea` | 수집할 태그 목록 |
| `--model` | `sonnet` | gatherer/writer 에이전트 모델 |

## 실행 절차

### Step 1: MCP / CLI 감지

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` — "공통 패턴 > MCP / CLI / 설치 안내 3단계 감지" 절차를 따릅니다.

### Step 2: retro-coordinator 스폰

```
Agent(
  subagent_type: "obsidian-nexus:retro-coordinator",
  model: "sonnet",
  prompt: "projects: {--projects 값 또는 미지정}
tags: {--tags 값}
model: {--model 값}
cwd: {현재 작업 디렉토리}
today: {YYYY-MM-DD}",
  description: "주간 회고 생성"
)
```

coordinator가 나머지 모든 흐름(인터뷰 → gatherer 병렬 → writer → 액션)을 처리합니다.

## 파이프라인

```
/obs-nexus:retro
       │
       ▼
retro-coordinator (Team Agent)
  ① nexus_list_projects → 프로젝트 목록
  ② AskUser: 프로젝트 선택
  ③-a nexus_search(weekly-retro, created_at) → 최근 회고 탐지
  ③-b nexus_get_metadata → period.to 추출
  ③-c nexus_search(tag_match_all) → 멱등성 체크
  ④ AskUser: 날짜 범위 선택 (period.to+1일 ~ 오늘 기본)
       │
       ├─ [병렬] retro-gatherer × N프로젝트
       │         nexus_search + nexus_get_section → JSON 요약
       │
       ▼
  retro-writer
    템플릿 기반 회고 문서 생성
    (weekly-retro + YYYY-W## 태그, period frontmatter 필수)
       │
       ▼
  ⑦ AskUser: 액션 아이템 TODO 문서 생성 여부
       │
       ▼
  obs-nexus index 재인덱싱
```

## 출력 파일

| 파일 | 조건 |
|------|------|
| `{vault}/retro/{YYYY}/{W##}.md` | 항상 (프로젝트별) |
| `{vault}/retro/{YYYY}/{W##}-summary.md` | 멀티 프로젝트 선택 시 |
| `{vault}/retro/{YYYY}/{W##}-actions.md` | 사용자 선택 시 |

## 날짜 탐지 로직

1. `nexus_search(tags: ["weekly-retro"], date_field: "created_at")` 로 최근 회고 탐지
2. `nexus_get_metadata` 로 해당 문서의 `period.to` frontmatter 읽기
3. `period.to + 1일 ~ 오늘` 을 기본 제안, 최근 4주 주차 목록 + 직접 입력도 제공

## 멱등성

동일 주차(`weekly-retro` + `YYYY-W##` 태그 AND 검색) 문서가 이미 존재하면
사용자에게 덮어쓸지 여부를 묻습니다.

## 핵심 의존성

- **nexus_search**: 태그 + 날짜 범위 검색, 최근 회고 탐지
- **nexus_get_metadata**: 회고 frontmatter에서 `period.to` 추출
- **nexus_get_section**: 문서 딥 읽기 (gatherer)
- **nexus_list_projects**: 프로젝트 목록 + CWD 기반 추천
- **Agent 도구**: gatherer 병렬 호출

## 관련 파일

- `$CLAUDE_PLUGIN_ROOT/agents/retro-coordinator.md`
- `$CLAUDE_PLUGIN_ROOT/agents/retro-gatherer.md`
- `$CLAUDE_PLUGIN_ROOT/agents/retro-writer.md`
- `$CLAUDE_PLUGIN_ROOT/templates/retro.md`
- `$CLAUDE_PLUGIN_ROOT/templates/retro-summary.md`
- `$CLAUDE_PLUGIN_ROOT/templates/retro-actions.md`
