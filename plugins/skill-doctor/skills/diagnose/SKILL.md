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

### 3. 스킬 파일 읽기 (구조 진단용)

diagnose 대상 스킬의 SKILL.md 파일을 찾아서 읽는다:
1. diagnose JSON의 profile에 skill_path가 있으면 그 경로 사용
2. 없으면 `.claude/skills/{스킬명}/SKILL.md` 에서 탐색
3. 없으면 `~/.claude/plugins/cache/*/*/skills/{스킬명}/SKILL.md` 패턴으로 마켓플레이스 캐시에서 탐색
4. 찾지 못하면 구조 진단은 스킵하고 시그널 진단만 수행

### 4. skill-doctor 에이전트 호출
Agent 도구로 플러그인 에이전트 `skill-doctor`를 호출한다 (diagnose JSON + 스킬 파일 내용 전달):
- `name="skill-doctor"` — 플러그인 에이전트는 agents/ 디렉토리의 파일명(확장자 제외)으로 매칭됨
- `description="skill-doctor 진단"`
- `prompt`에 diagnose JSON + 스킬 파일 내용을 포함

> 스킬 파일을 찾지 못한 경우 스킬 파일 부분을 제외하고 호출.

### 5. 결과 처리
- skill-doctor 출력의 리포트를 사용자에게 표시
- "실행 명령어" 섹션의 cli.py 명령어를 Bash로 실행
- 리포트를 `~/.claude/skill-doctor/reports/`에 저장

**소스 유형에 따른 분기:**
- **로컬 스킬** (`source: local`): level 3+일 때 `/skill-doctor:heal` 실행 추천
- **마켓플레이스 스킬** (`source: marketplace`): heal 불가 (외부 플러그인은 수정 대상이 아님). 리포트만 저장하고, 추후 해당 데이터를 기반으로 개선된 로컬 스킬 생성을 제안할 수 있음을 안내

소스 유형은 diagnose JSON 출력의 `source` 필드로 확인한다.

### 6. 다음 단계 추천

진단 결과에 따라 AskUserQuestion 도구로 다음 단계를 제안:

**Level 3+ 이슈 — 로컬 스킬인 경우:**
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

**Level 3+ 이슈 — 마켓플레이스 스킬인 경우:**
```yaml
questions:
  - question: '반복 문제가 발견되었지만 외부 플러그인 스킬이라 직접 수정할 수 없습니다. 리포트가 저장되었습니다.'
    header: '다음 단계'
    options:
      - label: 'suggest — 대체 로컬 스킬 제안'
        description: '축적된 리포트를 바탕으로 개선된 로컬 스킬 생성을 제안합니다'
      - label: 'report — 리포트 이력 확인'
        description: '이 스킬의 과거 진단 이력을 확인합니다'
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

## 시그널 기록

> **자동 수집 (Hook+Agent)**: 도구 실패, 사용자 메시지 등 raw 이벤트를 Hook이 수집하고, Stop 시 Claude가 유의미한 시그널만 판별하여 DB에 기록합니다.
> **수동 보조**: redo, manual_fix, clarify, blocked는 hook으로 감지하기 어려우므로, 발생 시 `/skill-doctor:record`로 수동 기록하면 데이터 품질이 향상됩니다.
