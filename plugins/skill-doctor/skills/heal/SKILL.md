---
name: heal
description: 진단된 문제를 자동으로 스킬 프롬프트에 반영할 때 사용 (스킬 수정, 자동 수정, heal, self-healing, 스킬 고쳐줘, 프롬프트 개선, 스킬 보완)
---

# skill-doctor 자동 수정 (heal)

CLI 경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`

## 실행 절차

### 1. 진단 데이터 확인

스킬명이 지정되면 바로 진단 데이터를 조회:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py diagnose --skill <name> --full
```

스킬명이 없으면 목록에서 health_score가 낮은 스킬을 보여주고 선택하게 한다:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py list
```

### 2. 에스컬레이션 레벨 확인

diagnose JSON의 cross_session.cause_type_counts에서 반복 횟수를 확인:
- 1회: "아직 반복 패턴이 아닙니다. 더 데이터가 쌓인 후 시도하세요." → 종료
- 2회: 리포트만 생성 (heal 불필요)
- **3회+: heal 대상** → 다음 단계 진행

### 3. 대상 스킬 파일 읽기

스킬 파일 경로를 찾는다:
1. skill_profiles의 skill_path 컬럼 확인
2. skill_path가 없으면 `.claude/skills/`, `.claude/plugins/` 에서 스킬명으로 탐색
3. 찾지 못하면 사용자에게 경로를 질문

스킬 파일(SKILL.md)을 Read 도구로 읽는다.

### 4. skill-healer 에이전트 호출

diagnose JSON + 스킬 파일 내용 + heal_tracking을 함께 전달:
```
Agent(
  description="skill-healer 수정 분석",
  prompt="다음 스킬 파일과 진단 데이터를 분석하여 수정 diff를 생성해주세요.\n\n## 스킬 파일 ({skill_path})\n{skill_content}\n\n## 진단 데이터\n{diagnose_json}\n\n## Heal 이력\n{heal_tracking_json}\n\n반복되는 cause_type에 대해 스킬 프롬프트의 어떤 부분을 어떻게 수정해야 하는지 구체적인 diff를 제안하세요. previous_heals가 있으면 이전과 다른 접근 방식을 사용하세요.",
  name="skill-healer"
)
```
> `skill-healer`는 셀프힐링 전문 에이전트로 diff 품질이 높고 검증 메타데이터를 함께 생성합니다.

### 5. 사용자 승인 + 적용

skill-healer 에이전트의 diff 제안을 사용자에게 표시:
```
## 수정 제안

파일: {skill_path}

변경 전:
> 기존 내용

변경 후:
> 수정 내용

변경 이유: {reason}
```

- **승인**: Edit 도구로 스킬 파일에 적용 → update-profile --resolve
- **거부**: update-profile --dismiss → 30일간 같은 이슈 재제안 안 함
- **수정 후 적용**: 사용자가 diff를 수정한 버전으로 적용

### 6. 적용 후 확인 (관찰 모드)

skill-healer가 출력한 "실행 명령어" 섹션의 CLI 명령을 실행한다.
`--heal-tracking` 옵션이 포함되어 있으므로 검증 메타데이터가 자동 저장됨:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py update-profile --skill "<name>" --health-score <new_score> --resolve "<cause_type>" --heal-tracking '<heal_tracking_json>'
```

리포트를 `~/.claude/skill-doctor/reports/`에 저장.

> **주의: resolve는 "완전 해결"이 아닌 "관찰 중" 상태.**
> 다음 3세션 내에 같은 cause_type이 재발하면, skill-doctor 에이전트가 "resolve 후 재발"로 감지하여:
> - resolved를 해제하고 다시 미해결로 복원
> - 이전 heal diff가 효과 없었음을 리포트에 명시
> - 새로운 접근의 diff를 제안 (이전 diff와 다른 방향)
>
> 이를 통해 **잘못된 heal이 자동 롤백**되고 다른 수정을 시도할 수 있다.

### 7. 다음 단계 추천

AskUserQuestion 도구로 다음 단계를 제안:

```yaml
questions:
  - question: '수정이 적용되었습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'dashboard — 전체 현황 확인'
        description: '수정 후 건강도 변화를 확인합니다'
      - label: 'diagnose {다른 스킬} — 다른 스킬 진단'
        description: '다른 건강도 낮은 스킬을 진단합니다'
      - label: 'report — 리포트 이력'
        description: '과거 진단/수정 이력을 확인합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

사용자 선택에 따라 해당 스킬을 실행한다.
