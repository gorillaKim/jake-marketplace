---
name: retro
description: 프로젝트별 decision/devlog/idea 문서를 날짜 범위로 수집하여 주간 회고 문서를 자동 생성하는 스킬. 멀티 프로젝트 병렬 처리 지원 (주간 회고, retro, weekly retro, 회고 생성, 주간 정리)
---

# 주간 회고 스킬 (`/doxus:retro`)

프로젝트별 `decision`, `devlog`, `idea` 태그 문서를 날짜 범위로 검색하고,
내용을 딥 요약하여 주간 회고 문서를 자동 생성합니다.

## 인터페이스

```
/doxus:retro
/doxus:retro --projects "A,B,C"
/doxus:retro --tags "decision,devlog,idea,bug"
/doxus:retro --model haiku
```

## 실행 절차

### Step 1: MCP / CLI 감지

→ `$CLAUDE_PLUGIN_ROOT/cli-reference.md` 참조.

### Step 2: retro-coordinator 스폰

```
Agent(
  subagent_type: "doxus:retro-coordinator",
  model: "sonnet",
  prompt: "projects: {--projects 값 또는 미지정}
tags: {--tags 값}
model: {--model 값}
cwd: {현재 작업 디렉토리}
today: {YYYY-MM-DD}",
  description: "주간 회고 생성"
)
```

coordinator가 나머지 모든 흐름을 처리합니다.

## 파이프라인

```
/doxus:retro
       │
       ▼
retro-coordinator
  ① doxus_list_projects → 프로젝트 목록
  ② AskUser: 프로젝트 선택
  ③ 최근 회고 탐지 + period.to 추출 + 멱등성 체크
  ④ AskUser: 날짜 범위 선택
       │
       ├─ [병렬] retro-gatherer × N프로젝트
       │         doxus_search + doxus_get_section → JSON 요약
       │
       ▼
  retro-writer → 템플릿 기반 회고 문서 생성
       │
       ▼
  ⑦ AskUser: 액션 아이템 TODO 문서 생성 여부
       │
       ▼
  재인덱싱: MODE=mcp → doxus_index_project(name=<PROJECT>) / MODE=cli → doxus index
```

## 출력 파일

| 파일 | 조건 |
|------|------|
| `{vault}/retro/{YYYY}/{W##}.md` | 항상 (프로젝트별) |
| `{vault}/retro/{YYYY}/{W##}-summary.md` | 멀티 프로젝트 선택 시 |
| `{vault}/retro/{YYYY}/{W##}-actions.md` | 사용자 선택 시 |

## 관련 파일

- `$CLAUDE_PLUGIN_ROOT/agents/retro-coordinator.md`
- `$CLAUDE_PLUGIN_ROOT/agents/retro-gatherer.md`
- `$CLAUDE_PLUGIN_ROOT/agents/retro-writer.md`
- `$CLAUDE_PLUGIN_ROOT/templates/retro.md`
