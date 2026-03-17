---
name: record
description: 스킬 사용 중 발생한 문제나 시그널을 수동 기록할 때 사용 (시그널 기록, record, 시그널 등록, 문제 기록, 스킬 피드백)
---

# skill-doctor 시그널 기록

CLI 경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`

## 시그널 타입 참조

| 타입 | CD 점수 | 의미 |
|------|---------|------|
| clarify | +0 | 에이전트가 사용자에게 질문 (정상 동작) |
| correct | +25 | 사용자가 에이전트의 판단을 수정 |
| redo | +40 | 작업 롤백/재시도 |
| tool_error | +15 | 도구 호출 실패 |
| cancelled | +50 | 사용자가 스킬 중도 취소 |
| manual_fix | +30 | 사용자가 직접 코드 수정 |
| blocked | +0 | 에이전트가 올바르게 멈춤 |

## cause_type 참조

**스킬 측** (CD 가산, 에스컬레이션 대상):
ambiguous_instruction, missing_precondition, scope_exceeded, output_mismatch, error_handling

**사용자 측** (CD 가산 안 함, 에스컬레이션 제외):
insufficient_context, user_preference, external_issue

## 실행 절차

### 1. 사용자에게 정보 수집

AskUserQuestion 도구로 구조화된 질문을 사용하여 정보를 수집:

**스킬 선택:**
```yaml
questions:
  - question: '어떤 스킬에 대한 시그널을 기록할까요?'
    header: '대상 스킬'
    options:
      # 현재 프로젝트의 스킬 목록을 동적으로 생성
      - label: '{skill_1}'
      - label: '{skill_2}'
      - label: '직접 입력'
        description: '목록에 없는 스킬명을 입력합니다'
    multiSelect: false
```

**시그널 타입 선택:**
```yaml
questions:
  - question: '어떤 종류의 이벤트가 발생했나요?'
    header: '시그널 타입'
    options:
      - label: 'correct — 판단 수정'
        description: '에이전트의 판단을 사용자가 수정 (+25)'
      - label: 'redo — 재시도'
        description: '작업을 롤백하고 재시도 (+40)'
      - label: 'manual_fix — 직접 수정'
        description: '사용자가 코드를 직접 수정 (+30)'
      - label: 'tool_error — 도구 오류'
        description: '도구 호출이 실패 (+15)'
      - label: 'cancelled — 중도 취소'
        description: '스킬을 중간에 취소 (+50)'
      - label: 'clarify — 질문 필요'
        description: '에이전트가 사용자에게 질문 (+0, 정상 동작)'
      - label: 'blocked — 올바른 중단'
        description: '에이전트가 올바르게 멈춤 (+0)'
    multiSelect: true
```

**원인 분류:**
```yaml
questions:
  - question: '문제의 원인은 무엇이었나요?'
    header: '원인 분류'
    options:
      - label: 'ambiguous_instruction — 모호한 지시'
        description: '스킬 프롬프트의 지시가 불명확'
      - label: 'output_mismatch — 출력 불일치'
        description: '기대한 출력과 실제 결과가 다름'
      - label: 'missing_precondition — 전제조건 누락'
        description: '필요한 선행 조건이 충족되지 않음'
      - label: 'scope_exceeded — 범위 초과'
        description: '스킬의 역할 범위를 벗어남'
      - label: 'error_handling — 에러 처리'
        description: '에러 상황에 대한 처리가 부족'
      - label: 'insufficient_context — 사용자 정보 부족'
        description: '사용자가 충분한 정보를 제공하지 않아 발생 (스킬 결함 아님)'
      - label: 'user_preference — 사용자 선호'
        description: '사용자 취향에 의한 수정, 스킬 기본 동작은 정상 (스킬 결함 아님)'
      - label: 'external_issue — 외부 환경 문제'
        description: '네트워크, 권한, 파일 부재 등 외부 요인 (스킬 결함 아님)'
    multiSelect: false
```

> **사용자 측 cause_type**(insufficient_context, user_preference, external_issue)은 CD 점수에 가산되지 않으며 에스컬레이션에서 제외됩니다.

이후 context와 cause_detail은 자유 텍스트로 추가 질문.

### 2. JSON 파일 생성

수집한 정보를 JSON으로 생성하여 `~/.claude/skill-doctor/tmp/` 에 저장:
```json
{
  "skill": "<스킬명>",
  "signals": [
    {
      "type": "<타입>",
      "context": "<상황 설명>",
      "action_taken": "<조치 내용>",
      "cause_type": "<원인 분류 (선택)>",
      "cause_detail": "<원인 상세 (선택)>"
    }
  ]
}
```

### 3. CLI로 기록
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py record --file <json_path>
```

### 4. 결과 표시 및 다음 단계 추천

CLI 출력의 session_id와 cd_score를 사용자에게 알려준다.

AskUserQuestion 도구로 다음 단계를 제안:

**cd_score >= 50인 경우:**
```yaml
questions:
  - question: 'CD 점수가 높습니다({cd_score}). 진단을 실행할까요?'
    header: '다음 단계'
    options:
      - label: 'diagnose {skill} — 즉시 진단'
        description: 'CD 점수가 높아 진단을 권장합니다'
      - label: 'dashboard — 전체 현황'
        description: '다른 스킬 상태도 확인합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

**cd_score < 50인 경우:**
```yaml
questions:
  - question: '시그널이 기록되었습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'record — 추가 시그널 기록'
        description: '다른 시그널도 기록합니다'
      - label: 'dashboard — 전체 현황'
        description: '스킬 건강도를 확인합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

사용자 선택에 따라 해당 스킬을 실행한다.
