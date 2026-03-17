---
name: diagnose
description: 스킬이 잘 동작하지 않거나, 같은 문제가 반복되거나, 스킬 품질을 점검할 때 사용 (스킬 진단, 스킬 문제, skill-doctor, diagnose, 스킬이 이상해, 스킬 개선, 스킬 건강)
---

# skill-doctor 진단

CLI 경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`
CLI 문서: `${CLAUDE_PLUGIN_ROOT}/docs/CLI_REFERENCE.md`

## 실행 절차

### 1. 스킬 목록 조회
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py list
```
사용자에게 목록을 보여주고 진단할 스킬을 선택하게 한다. 사용자가 이미 스킬명을 지정했으면 이 단계 스킵.

### 2. 진단 데이터 추출
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py diagnose --skill <name>
```
--session 생략하면 최근 세션 자동 선택.

### 2.5. 스킬 파일 읽기 (구조 진단용)

diagnose 대상 스킬의 SKILL.md 파일을 찾아서 읽는다:
1. diagnose JSON의 profile에 skill_path가 있으면 그 경로 사용
2. 없으면 `.claude/skills/{스킬명}/SKILL.md`, `.claude/plugins/` 등에서 탐색
3. 찾지 못하면 구조 진단은 스킵하고 시그널 진단만 수행

### 3. skill-doctor 에이전트 호출
diagnose 출력 JSON(heal_tracking 포함) + 스킬 파일 내용을 Agent 도구로 `skill-doctor` 에이전트에 전달:
```
Agent(
  description="skill-doctor 진단",
  prompt="다음 diagnose JSON과 스킬 파일을 분석하여 진단 리포트를 생성해주세요:\n\n## Diagnose JSON\n{diagnose_json}\n\n## 스킬 파일 ({skill_path})\n{skill_content}\n\ndiagnose JSON에 heal_tracking이 포함되어 있으면 active heal의 재발 여부를 확인하고, 재발 시 --fail-heal 명령어를 실행 명령어에 포함하세요.\n스킬 파일이 포함되어 있으면 구조 진단도 함께 수행하세요.",
  name="skill-doctor"
)
```
> 플러그인 에이전트는 name 기반으로 호출. subagent_type이 아닌 name 필드 사용.
> 스킬 파일을 찾지 못한 경우 스킬 파일 부분을 제외하고 호출.

### 4. 결과 처리
- skill-doctor 출력의 리포트를 사용자에게 표시
- "실행 명령어" 섹션의 cli.py 명령어를 Bash로 실행
- level 3+: diff는 **생성하지 않음** → 대신 `/skill-doctor:heal` 실행을 추천 (skill-healer가 전담)
- 리포트를 `~/.claude/skill-doctor/reports/`에 저장

### 5. 다음 단계 추천

진단 결과에 따라 AskUserQuestion 도구로 다음 단계를 제안:

**Level 3+ 이슈가 있는 경우:**
```yaml
questions:
  - question: '반복되는 문제가 발견되었습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'heal {skill} — 자동 수정'
        description: '진단된 문제를 스킬 프롬프트에 자동 반영합니다'
      - label: 'report — 리포트 확인'
        description: '과거 진단 이력과 비교합니다'
      - label: 'dashboard — 전체 현황'
        description: '다른 스킬 상태도 확인합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

**경미한 이슈만 있는 경우:**
```yaml
questions:
  - question: '진단이 완료되었습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'dashboard — 전체 현황'
        description: '다른 스킬 상태도 확인합니다'
      - label: 'record — 추가 시그널 기록'
        description: '놓친 시그널을 수동으로 기록합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

사용자 선택에 따라 해당 스킬을 실행한다.
