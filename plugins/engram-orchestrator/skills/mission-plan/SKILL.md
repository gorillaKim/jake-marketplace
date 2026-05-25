---
name: mission-plan
description: 대형 피처 또는 신규 분기 목표 수립 시, 미션을 생성하고 하위 에픽과 이슈들을 계층 구조로 일괄 수립하는 스킬. 트리거 — "미션 계획", "로드맵", "분기 목표 설정"
tools:
  - mcp__engram__sprint_current
  - mcp__engram__mission_create
  - mcp__engram__mission_list
  - AskUserQuestion
  - Agent
---

# Mission Plan

## 목적

대형 피처 개발이나 새 프로젝트 시작 시, 미션 단위를 먼저 수립하고 산하에 여러 에픽과 이슈/태스크를 로드맵 형태로 자동 생성 및 연동하기 위한 스킬입니다.
이 스킬을 활용하면 Mission → Epic → Issue → Task 로 이어지는 계층 구조를 일관되게 생성할 수 있습니다.

## 트리거 게이트 — 다음 중 하나가 감지될 때 로드

사용자 요청에 대규모 마일스톤 설계 의도가 감지될 때:
- `"미션 계획"`, `"미션 수립"`, `"로드맵"`, `"분기 목표 설정"`, `"마일스톤 계획"`

## 실행 절차

### 1) 컨텍스트 수집

`sprint_current()` 및 `mission_list()`를 호출하여 현재 활성 스프린트와 미션 목록을 파악하고, 신규 수립할 로드맵의 일정 범위를 정의합니다.

### 2) 미션 정의 수립

사용자에게 신규 미션의 제목, 설명, 목표를 질의하여 정보를 취합한 뒤, `mission_create`를 사용하여 미션을 수립합니다.

```
# 예시: 2분기 결제 시스템 고도화 미션 생성
mission_create(
  sprint_id=<active_sprint_id>,
  title="2분기 결제 시스템 고도화",
  description="결제 수단 다변화 및 안정성 보장을 위한 종합 개편 미션"
) → 반환된 mission_id 확보
```

### 3) Analyzer 호출을 통한 계층적 자동 계획

확보된 `mission_id`를 analyzer 서브에이전트에 전달하여 하위 에픽 및 이슈 분할을 일임합니다.

```
Agent(
  subagent_type='engram-orchestrator:engram-analyzer',
  prompt=(
    f"사용자의 대형 작업 요구사항을 분할하여 계획을 수립하세요.\n"
    f"반드시 새로 수립된 미션 ID {mission_id} 하위에 에픽들을 매핑/생성하고,\n"
    f"각 에픽 산하의 하위 이슈와 태스크들을 쪼개어 등록해야 합니다."
  )
)
```

### 4) 결과 보고

analyzer 가 수립을 마치면, 생성된 미션 하위의 에픽 구조와 이슈 목록을 요약하여 사용자에게 보고하고, `engram-leader`를 시작할 준비가 되었음을 안내합니다.

## CLI fallback (MCP 미지원 환경)

`mcp__engram__*` 가 없으면 셸 호출을 통해 흐름을 진행합니다:

```bash
# 1. 미션 수립
engram mission create --sprint 3 --title "2분기 결제 시스템 고도화" --json
# 생성된 ID 확인 (예: 19)

# 2. analyzer 소환하여 해당 미션 하위 에픽/이슈 분할 지시
# (analyzer CLI fallback 흐름으로 인계)
```
