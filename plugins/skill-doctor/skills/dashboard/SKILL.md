---
name: dashboard
description: 추적 중인 스킬들의 건강 상태를 한눈에 확인할 때 사용 (대시보드, 스킬 현황, 스킬 목록, health, 스킬 상태, 전체 스킬, dashboard)
---

# skill-doctor 대시보드

CLI 경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`

## 실행 절차

### 1. 스킬 목록 조회
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py list
```
현재 프로젝트 기준으로 추적 중인 스킬 목록을 조회한다.

전체 프로젝트를 보고 싶다고 사용자가 요청하면:
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py list --all-projects
```

### 2. 대시보드 표시

조회 결과를 아래 형식으로 표시:

```
## 🏥 skill-doctor 대시보드

| 스킬 | 프로젝트 | Health | 세션 수 | 마지막 진단 | 상태 |
|------|---------|--------|---------|------------|------|
| {skill} | {project} | {score}/100 | {sessions} | {date} | {emoji} |

상태 기준: 🟢 80+ | 🟡 50-79 | 🔴 <50 | ⚪ 미진단
```

### 3. 다음 단계 추천

대시보드 결과에 따라 AskUserQuestion 도구로 상황별 다음 단계를 제안:

**스킬이 없는 경우:**
```yaml
questions:
  - question: '아직 기록된 스킬이 없습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'suggest — 자동화 제안 받기'
        description: '반복 패턴을 분석하여 새 스킬 생성을 제안합니다'
      - label: 'create — 새 스킬 만들기'
        description: '새 스킬/에이전트/규칙을 직접 생성합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

**health_score < 50인 스킬이 있는 경우:**
```yaml
questions:
  - question: '건강도가 낮은 스킬이 있습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'diagnose {lowest_skill} — 진단 실행'
        description: '가장 건강도가 낮은 스킬을 진단합니다'
      - label: 'heal {lowest_skill} — 자동 수정'
        description: '이미 진단된 스킬의 문제를 자동 수정합니다'
      - label: 'report — 리포트 조회'
        description: '과거 진단 이력을 확인합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

**모든 스킬이 정상(80+)인 경우:**
```yaml
questions:
  - question: '모든 스킬이 건강합니다! 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'suggest — 새 자동화 제안'
        description: '반복 패턴을 분석하여 새 스킬을 제안합니다'
      - label: 'report — 리포트 이력'
        description: '과거 진단 이력을 확인합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

사용자 선택에 따라 해당 스킬을 실행한다.
