---
name: init
description: 프로젝트에 skill-doctor를 설정하고 CLAUDE.md에 시그널 기록 지침을 추가할 때 사용 (skill-doctor 설정, init, 초기화, skill-doctor 시작, 셋업, skill-doctor 설치)
---

# skill-doctor 초기화

CLI 경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`

## 실행 절차

### 1. 데이터 디렉토리 초기화
```bash
mkdir -p ~/.claude/skill-doctor/{tmp,reports}
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py list
```
list 명령이 DB를 자동 생성한다. 에러 없으면 정상.

### 2. .claude/CLAUDE.md 확인 및 수정

프로젝트 루트의 `.claude/CLAUDE.md` 파일을 확인한다.

**파일이 없으면**: `.claude/` 디렉토리와 `CLAUDE.md`를 생성한다.
**파일이 있으면**: `<!-- skill-doctor -->` 마커가 있는지 확인한다.

마커가 없으면 파일 끝에 아래 내용을 추가:

```markdown
<!-- skill-doctor -->
## skill-doctor 시그널 기록

스킬 실행 중 이벤트(redo/tool_error/cancelled/clarify/correct/manual_fix/blocked) 발생 시 type+cause_type+cause_detail을 메모리에 누적한다.
스킬 종료 시 누적된 시그널을 아래 JSON 형식으로 Write(~/.claude/skill-doctor/tmp/sd-session-{timestamp}.json)로 저장한다:

```json
{
  "skill": "스킬명",
  "skill_path": ".claude/skills/스킬명/SKILL.md",
  "signals": [
    {"type": "correct", "context": "상황 설명", "action_taken": "조치", "cause_type": "ambiguous_instruction", "cause_detail": "구체적 원인"}
  ]
}
```

저장 후 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py record --file <path>`로 기록한다.
cd_score ≥ 50이면 `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py diagnose --skill <스킬명>` → skill-doctor 서브에이전트를 호출하여 진단한다.
시그널이 없었으면 `"signals": []`(빈 배열)로 기록한다 — 정상 실행의 긍정적 데이터.

**원인 귀속**: 시그널의 원인이 스킬 결함인지 사용자 측 요인인지 판단하여 cause_type을 기록한다.
- **스킬 측** (CD 가산): ambiguous_instruction, missing_precondition, scope_exceeded, error_handling, output_mismatch
- **사용자 측** (CD 가산 안 함): insufficient_context, user_preference, external_issue
- **clarify**(질문)는 정상 동작이므로 CD +0.

상세: `${CLAUDE_PLUGIN_ROOT}/docs/signal-recording.md` 참조
<!-- /skill-doctor -->
```

마커가 이미 있으면 "이미 설정되어 있습니다" 안내 후 스킵.

### 3. 설치 확인 리포트

```
## skill-doctor 초기화 완료

| 항목 | 상태 |
|------|------|
| 데이터 디렉토리 | ✅ ~/.claude/skill-doctor/ |
| DB | ✅ skill-doctor.db |
| CLAUDE.md | ✅ 시그널 기록 지침 추가됨 |
| 플러그인 | ✅ skill-doctor@jake-plugins |

사용 가능한 명령어:
- `/skill-doctor:dashboard` — 스킬 건강도 현황
- `/skill-doctor:diagnose <스킬명>` — 특정 스킬 진단
- `/skill-doctor:heal <스킬명>` — 자동 수정
```

### 4. 다음 단계 추천

AskUserQuestion 도구로 다음 단계를 제안:

```yaml
questions:
  - question: '초기화가 완료되었습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'dashboard — 스킬 현황 확인'
        description: '현재 추적 중인 스킬들의 건강도를 확인합니다'
      - label: 'suggest — 자동화 제안 받기'
        description: '반복 패턴을 분석하여 새 스킬 생성을 제안합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

사용자 선택에 따라 해당 스킬을 실행한다.
