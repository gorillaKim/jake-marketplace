# 시그널 기록 규칙

스킬 실행 중 아래 이벤트 발생 시 메모리에 누적하고, 스킬 종료 시 기록한다.

**제외**: `skill-doctor` 플러그인 자체의 스킬(`/skill-doctor:diagnose`) 실행 시에는 시그널을 기록하지 않는다. 자기 자신을 진단하는 순환을 방지.

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
| `list [--all-projects]` | 기록된 스킬 목록 + health_score 조회 |
| `diagnose --skill <name> [--session <id>] [--full] [--all-projects]` | 스킬 진단 데이터 JSON 출력. --session 생략 시 최근 세션 자동 선택. |
| `update-profile --skill <name> --health-score <N>` | 프로파일 업데이트. --resolve, --dismiss, --heal-tracking, --fail-heal, --confirm-heal 옵션. |

상세 사용법: `docs/CLI_REFERENCE.md` 참조.

## 스킬 종료 시 기록 절차

1. Write 도구로 `~/.claude/skill-doctor/tmp/sd-session-{timestamp}.json` 생성:
```json
{
  "skill": "스킬명",
  "signals": [
    {"type": "correct", "context": "한 줄 설명", "cause_type": "ambiguous_instruction", "cause_detail": "원인"}
  ]
}
```
시그널이 없으면 `"signals": []` (빈 배열도 기록 대상 — "완벽한 실행"으로 기록됨).

> **중요**: 빈 배열 기록은 "시그널이 없었다"는 **긍정적 데이터**이다. 시그널을 누락하면 안 되지만, 정말 문제 없이 실행된 경우에도 반드시 빈 배열로 기록하여 "이 세션은 정상이었다"를 명시한다. 이를 통해 health_score의 avg_cd_last_3 계산이 정확해진다.

2. Bash 실행:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py record --file ~/.claude/skill-doctor/tmp/sd-session-{timestamp}.json
```

3. 출력의 `cd_score`가 50 이상이면:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py diagnose --skill <스킬명>
```
출력된 JSON으로 `skill-doctor` 에이전트를 호출(`Agent(name="skill-doctor")`)하여 진단을 수행한다.
