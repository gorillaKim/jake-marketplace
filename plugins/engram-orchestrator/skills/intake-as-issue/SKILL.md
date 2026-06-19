---
name: intake-as-issue
description: 사용자가 구현/작업/수정 요청을 했을 때, 즉시 코드 변경에 들어가지 말고 Engram 이슈로 등록할지 먼저 확인한 뒤 engram-analyzer 를 호출한다. 트리거 — 다단계 변경이 명백한 작업 요청 ("구현해줘", "추가해줘", "리팩터링", "마이그레이션" 등). 1줄 수정/단순 조회/명시적 즉시 처리 지시는 제외.
tools:
  - mcp__engram__sprint_current
  - mcp__engram__mission_list
  - mcp__engram__session_restore
  - AskUserQuestion
  - Agent
---

# Intake as Issue

## 목적

사용자의 비정형 작업 요청을 곧바로 손대지 말고, **Engram 이슈로 분할·등록한 뒤** 진행하기 위한 게이트.
이슈로 등록하면:
- analyzer 가 작업을 적절히 쪼개고 우선순위와 의존성을 부여
- leader 가 워커에게 분배하고 정체를 감시
- 모든 변경이 issue/task/note 로 추적

## 트리거 게이트 — 다음 **모두** 만족 시에만 로드

1. 사용자 요청에 작업 의도 표현이 있다 ("구현/작업/추가/만들/리팩터링/마이그레이션/도입/제거").
2. 변경 규모가 **2개 이상의 단위 작업으로 자연스럽게 쪼개진다** (한 함수 수정만으로 끝나지 않는다).

## 트리거 제외 — 다음 중 하나라도 해당하면 즉시 처리

- 단발성 텍스트 편집: "이 줄 띄어쓰기 고쳐", "변수 이름만 바꿔", "오타 수정"
- 단순 조회/탐색: "X 가 어디 있어?", "Y 어떻게 동작해?"
- 명시적 즉시 처리 지시: "이슈로 만들지 말고 그냥 해줘", "빨리"
- 한 파일·한 함수 안에서 끝나는 게 명백한 수정
- 사용자가 이미 이슈 ID 를 들고 와서 처리만 요청 ("이슈 #142 작업해줘") — worker 직접 호출

## 실행 모드 판단 — solo-track vs 팀(analyzer→leader/worker)

작업을 **누가 처리할지**는 [실행 모드 라우팅 (solo-track vs 팀)](../../README.md#실행-모드-라우팅-solo-track-vs-팀) 기준으로 판단한다. 판단은 두 시점에서 이뤄진다:

**(1) 사전(pre-analysis) — 요청 텍스트만으로 명백할 때**
요청만 봐도 **단일 이슈·한 PR·병렬 이득 없음**이 분명하면(예: 함수 1개 리네이밍, 문서 파일 몇 개 추가, 설정 한 곳 변경) analyzer 분할 자체가 오버킬이므로 **곧장 solo-track 추천**:
```
이 작업은 한 PR 분량(독립 task 2~3개)으로 보입니다.
analyzer/leader/worker 분리 대신 solo-track(직접 처리 + 기록)으로 진행하면
토큰과 시간을 절반 이하로 줄일 수 있습니다.
  (a) solo-track 으로 바로 진행 (Recommended)
  (b) analyzer 로 이슈 분할 후 팀 처리
```
반대로 **진짜 복잡한 상황**(독립적이고 무거운 이슈가 동시에 여럿 → 병렬 이득 / 파일 충돌로 worktree 격리 필요 / 멀티 LLM 라우팅)이 명백할 때만 곧장 analyzer→팀 경로. 그 외엔 solo 를 기본으로.

**(2) 사후(post-analysis) — 분할해 봐야 규모가 드러날 때 (권장)**
모호하면 일단 `engram-analyzer` 를 호출하고, analyzer 가 반환하는 `RECOMMENDED_MODE`(solo|team)에 따라 라우팅한다(아래 실행 절차 3) 참조). analyzer 가 이슈 수·병렬 폭·충돌 위험을 실제로 산출하므로 가장 정확하다.

### 경계 케이스 예시 카드 (2~3 task / 한 PR 구간)

게이트 통과 여부와 solo vs team 이 헷갈리는 **중간 경계**는 아래 카드로 판단한다. **공통 원칙: 직렬로 처리 가능하면 solo, 동시 병렬 이득·파일 충돌 회피·멀티 LLM 중 하나가 명확할 때만 team.** (가장 흔한 실수는 solo 로 충분한데 team 을 고르는 false-positive 다.)

| # | 시나리오 | 규모 | 라우팅 | 이유 |
|---|---------|------|--------|------|
| 1 | 함수 1개 리네이밍 + 호출처 N곳 업데이트 | 2~3 task, 여러 파일이나 **직렬** | **solo-track** | 파일이 여럿이어도 한 작업 흐름·충돌 없음. 병렬 이득 없음. |
| 2 | 문서 파일 3~5개 신규 추가 (가이드/ADR 등) | 3~5 task, 독립 파일 | **solo-track** | 가벼운 직렬 작업. analyzer 분할은 오버킬. |
| 3 | 한 모듈에 엔드포인트 1개 + 테스트 + 문서 | 3 task, 같은 모듈 | **solo-track** | 동일 모듈이라 순차가 안전(충돌 위험). 한 PR 분량. |
| 4 | 서로 다른 모듈의 독립 기능 4~5개 동시 구현 | 4~5 이슈, 상호 독립·무거움 | **team (analyzer→leader)** | 동시 병렬 spawn 이 전체 시간 단축 + worktree 격리 이득. |
| 5 | 같은 파일을 여러 이슈가 동시에 수정 | 다중 이슈, **같은 파일** | **solo-track (직렬)** | 병렬이면 충돌. 직렬 solo 가 오히려 안전·저비용. |
| 6 | 오타/한 줄 수정, 단순 조회 | 1 task 이하 | **직접 처리** (게이트 제외) | 이슈화 마찰 > 추적 이득. |

> 카드 4 만 team, 나머지는 solo 또는 직접 처리다. **"이슈가 여러 개"는 team 의 근거가 아니다** — 직렬 처리 가능하면 solo. team 의 진짜 근거는 *동시 병렬 이득 / worktree 격리 / 멀티 LLM* 셋 중 하나가 명확할 때뿐이다. (SSOT: [실행 모드 라우팅](../../README.md#실행-모드-라우팅-solo-track-vs-팀))

## 강제 트리거 (게이트 무시)

사용자가 `"이슈로"`, `"issue 로"`, `"engram 에 등록"` 같은 표현을 명시했으면 위 게이트 무시하고 즉시 analyzer 호출. AskUserQuestion 도 생략.

## 실행 절차

### 1) 작업 요청 정리

사용자 요청을 1~3문장으로 재서술해, **무엇을 / 왜** 가 명확한 형태로 정리한다.

### 2) 이슈화 확인

`AskUserQuestion` 으로:

```
질문: "이 작업을 Engram 이슈로 만들어 처리할까요?"
옵션:
  - "예 (Recommended) — analyzer 가 분할/등록 후 작업 시작"
  - "아니오 — 지금 바로 처리"
```

### 3) 분기

- **예**: 
  1. `sprint_current` 및 `mission_list`를 호출하여 현재 활성 스프린트와 미션 목록을 파악하고, 사용자 요청이 기존의 특정 미션과 연계되어 있는지 분석합니다.
  2. `engram-analyzer`를 spawn 할 때, 파악된 미션 ID를 `hint_mission_id`로 프롬프트에 포함하여 전달합니다. 만약 새로운 미션(대형 피처 출시 목표 등)이 요구된다면 프롬프트에 "신규 미션 생성 필요" 명세를 포함합니다.
  3. `Agent(subagent_type='engram-orchestrator:engram-analyzer', prompt=<정리된 요청 + project_key 힌트 + hint_mission_id 및 미션 힌트>)` 호출 →
     analyzer 가 ready 이슈를 생성하고 `RECOMMENDED_MODE`(solo|team) + 근거를 반환.
  4. **실행 모드 라우팅** — analyzer 의 `RECOMMENDED_MODE` 에 따라 진행 ([기준](../../README.md#실행-모드-라우팅-solo-track-vs-팀)):
     - `solo` → 이슈 ID 목록 보고 후 **`solo-track` 으로 바로 이어 진행** (`solo-track` 에 `issue_id` 전달 = Step A.continue). 저비용이므로 추가 확인 불필요.
     - `team` → 워커 N개 spawn 은 비용이 크므로 **추천 + `AskUserQuestion` 으로 확인**:
       ```
       질문: "이슈 N건이 등록됐습니다(병렬 가능 M건). leader 로 팀 처리를 시작할까요?"
       옵션: "예 — leader 트리거 (Recommended)" / "아니오 — 이슈만 두고 대기"
       ```
       "예" → `engram-leader` 트리거. (사용자가 이미 즉시 진행을 명시했으면 확인 생략하고 바로 leader)
- **아니오**: 이슈 생성 없이 즉시 작업. 추가 권유 없음 (마찰 최소화).

## 주의

- analyzer 호출 시 `project_key` 를 같이 전달. 모르면 analyzer 의 결정 절차에 위임.
- 이 스킬은 한 세션에서 같은 요청에 두 번 트리거되지 않는다. 한 번 "아니오" 면 그 세션에서는 더 묻지 않음.
- 게이트 통과/제외 판단이 모호하면 게이트 제외 쪽으로 (즉, 직접 처리). false-positive 마찰이 false-negative 누락보다 비용 크다.
