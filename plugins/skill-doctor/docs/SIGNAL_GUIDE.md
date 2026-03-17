# skill-doctor 시그널 기록 가이드

## 이벤트 유형 (type)

| type | 점수 | 감지 | 설명 |
|---|---|---|---|
| `clarify` | +0 | 확실 | AskUserQuestion 호출 (정상 동작, 감점 아님) |
| `correct` | +25 | best effort | 사용자가 에이전트 판단을 수정 |
| `redo` | +40 | 확실 | 같은 작업 재시도 |
| `tool_error` | +15 | 확실 | 도구 에러 반환 |
| `cancelled` | +50 | 확실 | 스킬 중도 취소 |
| `manual_fix` | +30 | best effort | 사용자가 직접 코드 수정 |
| `blocked` | +0 | 확실 | 올바르게 멈춤 |

> **clarify는 감점이 아닙니다.** 스킬이 AskUserQuestion으로 사용자에게 질문하는 것은 모호성을 해소하는 **올바른 행동**입니다. clarify 시그널은 통계 추적용으로만 기록됩니다.

## 원인 유형 (cause_type, nullable)

### 스킬 측 원인 (스킬 개선 대상)
| cause_type | 설명 |
|---|---|
| `ambiguous_instruction` | 스킬 프롬프트의 지시가 모호 |
| `missing_precondition` | 스킬이 전제조건을 검증하지 않음 |
| `scope_exceeded` | 스킬 범위 정의가 불명확 |
| `error_handling` | 예외 상황 미처리 |
| `output_mismatch` | 결과물 포맷/품질이 기대와 다름 |

### 사용자 측 원인 (스킬 결함 아님, CD 가중치 0)
| cause_type | 설명 |
|---|---|
| `insufficient_context` | 사용자가 충분한 정보를 제공하지 않음 |
| `user_preference` | 사용자 개인 선호에 의한 수정 (스킬 기본 동작은 정상) |
| `external_issue` | 외부 환경 문제 (네트워크, 권한, 파일 부재 등) |

### 귀속(attribution) 판단 기준

시그널 기록 시 원인이 **스킬 결함인지 사용자 측 요인인지** 반드시 판단:

| 상황 | 귀속 | 예시 |
|------|------|------|
| 스킬이 같은 상황에서 매번 다르게 판단 | 스킬 | 복합 변경 시 타입 판단 불일치 |
| 사용자가 정보를 덜 줘서 추가 질문 | 사용자 | 티켓 번호 미제공 → 질문 |
| 사용자 취향으로 결과 수정 | 사용자 | "나는 이 경우 fix보다 refactor 선호" |
| 스킬 프롬프트에 명시된 규칙 위반 | 스킬 | 50자 제한 규칙 있는데 초과 |
| 외부 도구 오류 | 외부 | git 권한 오류, 네트워크 타임아웃 |

**사용자 측 cause_type은 CD 점수에 가산되지 않으며, 에스컬레이션 반복 횟수에도 포함되지 않는다.**

## 입력 JSON 형식

```json
{
  "skill": "스킬명",
  "skill_path": "스킬 파일 경로 (선택, 예: .claude/skills/my-skill/SKILL.md)",
  "signals": [
    {
      "type": "correct",
      "context": "한 줄 설명",
      "action_taken": "한 줄 조치",
      "cause_type": "ambiguous_instruction",
      "cause_detail": "구체적 원인"
    }
  ]
}
```

- signals 빈 배열 허용 (완벽한 실행)
- cause_type, cause_detail은 nullable
- context, action_taken은 한 줄 이내

## 스킬 프롬프트에 추가할 3줄

```
## 시그널 기록
이벤트(redo/tool_error/cancelled/clarify/correct/manual_fix/blocked) 발생 시 type+cause_type+cause_detail 누적.
종료 시 Write(~/.claude/skill-doctor/tmp/sd-session-{ts}.json) → python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py record --file <path>.
cd_score ≥ 50이면 python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py diagnose → skill-doctor 서브에이전트 호출.
```
