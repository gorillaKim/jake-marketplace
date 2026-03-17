# 시그널 기록 규칙

## 수집 방식 (3단계)

skill-doctor는 세 가지 방식으로 시그널을 수집한다:

| 방식 | 시그널 | 신뢰도 | 동작 |
|------|--------|--------|------|
| **Hook (자동)** | `tool_error`, `cancelled`, `correct` | 시스템 레벨 / best-effort | 플러그인 훅이 자동 감지. 설정 불필요 |
| **수동 (/record)** | 모든 타입 | 높음 | 사용자가 직접 기록. 가장 정확한 데이터 |
| **CLAUDE.md (보조)** | `redo`, `manual_fix`, `clarify`, `blocked` | best-effort | init에서 선택적 설정. Hook이 감지 못하는 시그널 보조 수집 |

### Hook 기반 자동 수집 (signal-collector.py)

### Hook + Agent 하이브리드 수집 (signal-collector.py)

**Phase 1 — Hook이 raw 이벤트 수집** (시스템 레벨, 판단 없음):

| 훅 이벤트 | 수집 내용 |
|-----------|----------|
| `PostToolUseFailure` | 도구명, 에러 메시지, is_interrupt — 모든 도구 실패를 raw 기록 |
| `UserPromptSubmit` | 사용자 메시지 텍스트 — 모든 메시지를 raw 기록 |
| `SubagentStart/Stop` | 스킬명 추적 (agent_type 필드) |

raw 이벤트는 `~/.claude/skill-doctor/active/{session_id}.json`에 세션별 누적.

**Phase 2 — Stop 시 Claude에게 분류 요청** (agent 레벨, 의미 판단):

`Stop` 훅에서 누적된 raw 이벤트를 `additionalContext`로 Claude 컨텍스트에 주입.
Claude가 아래 기준으로 유의미한 시그널만 판별 + cause_type 귀속:

- 정상적 탐색 실패(grep 결과 없음 등) → 무시
- 사용자 단순 대화/질문 → 무시
- 스킬 프롬프트의 모호성/누락으로 인한 실패 → 기록
- 유의미한 시그널 없으면 → 아무것도 안 함

**Phase 3 — Claude가 DB에 기록**:

판단된 시그널을 `tmp/sd-session-{ts}.json`으로 Write 후 `cli.py record`로 DB 기록.

## 이벤트 감지

| type | 감지 시점 | CD 점수 |
|---|---|---|
| `redo` | 같은 작업을 재시도할 때 | +40 |
| `tool_error` | 도구 호출이 에러를 반환할 때 | +15 |
| `cancelled` | 사용자가 스킬을 중도 취소할 때 | +50 |
| `clarify` | AskUserQuestion을 호출할 때 | **+0** (정상 동작) |
| `correct` | 사용자가 "아니", "그거 말고" 등으로 판단을 수정할 때 (best effort) | +25 |
| `manual_fix` | 사용자가 직접 코드를 수정할 때 (best effort) | +30 |
| `blocked` | 에이전트가 올바르게 멈출 때 | +0 |

> `clarify`는 감점이 아닙니다. 모호할 때 질문하는 것은 올바른 행동입니다.

각 이벤트에 원인이 있으면 `cause_type`과 `cause_detail`도 기록.

### 원인 귀속 (attribution)

시그널 기록 시 **스킬 결함 vs 사용자 측 요인**을 반드시 판단:

**스킬 측** (CD 가산, 에스컬레이션 대상):
- `ambiguous_instruction`, `missing_precondition`, `scope_exceeded`, `error_handling`, `output_mismatch`

**사용자 측** (CD 가산 안 함, 에스컬레이션 제외):
- `insufficient_context` — 사용자가 충분한 정보 미제공
- `user_preference` — 사용자 개인 선호에 의한 수정
- `external_issue` — 외부 환경 문제

**판단 기준**: 같은 상황에서 스킬이 일관되게 잘못 판단하면 스킬 결함. 사용자가 정보를 덜 줬거나 취향 차이면 사용자 측.

## CLI 명령어

CLI 경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`

| 명령어 | 용도 |
|---|---|
| `record --file <path>` | 세션 시그널을 DB에 기록. CD 점수 자동 계산. 입력 파일 자동 삭제. |
| `list [--all-projects]` | 기록된 스킬 목록 + health_score + source + plugin_name 조회 |
| `diagnose --skill <name> [--session <id>] [--full] [--all-projects]` | 스킬 진단 데이터 JSON 출력 (source, plugin_name 포함). --session 생략 시 최근 세션 자동 선택. |
| `discover-marketplace [--prune]` | 설치된 마켓플레이스 플러그인 스킬 자동 발견. --prune으로 삭제된 플러그인 정리. |
| `update-profile --skill <name> --health-score <N>` | 프로파일 업데이트. --resolve, --dismiss, --heal-tracking, --fail-heal, --confirm-heal 옵션. |

상세 사용법: `docs/CLI_REFERENCE.md` 참조.

## 기록 절차

### 자동 (Hook 기반 — 기본)

플러그인 훅(`hooks/hooks.json`)이 시스템 레벨에서 자동 수집:
1. `PostToolUseFailure` → `tool_error` / `cancelled` 시그널 자동 감지
2. `UserPromptSubmit` → `correct` best-effort 패턴 매칭
3. `SubagentStart/Stop` → 스킬명 추적
4. `Stop` / `SessionEnd` → 누적 시그널을 `tmp/sd-session-{ts}.json`으로 flush → `cli.py record` 자동 호출

시그널이 없는 세션은 기록하지 않음 (hook은 문제가 있는 세션만 기록).

### 수동 (`/skill-doctor:record`)

hook으로 감지하기 어려운 시그널(`redo`, `manual_fix`, `clarify`, `blocked`)이나, 더 정확한 `cause_type`/`cause_detail`을 기록하고 싶을 때 사용.

입력 JSON 형식:
```json
{
  "skill": "스킬명",
  "skill_path": "스킬 파일 경로 (선택)",
  "signals": [
    {"type": "correct", "context": "한 줄 설명", "cause_type": "ambiguous_instruction", "cause_detail": "원인"}
  ]
}
```

### 보조 (CLAUDE.md 지침 — 선택)

`/skill-doctor:init`에서 설정 가능. hook이 감지하지 못하는 `redo`, `manual_fix` 등의 보조 수집용.
