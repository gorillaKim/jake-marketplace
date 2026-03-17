---
name: report
description: 과거 스킬 진단 결과를 확인하거나 리포트 이력을 조회할 때 사용 (진단 리포트, report, 리포트 조회, 진단 이력, 과거 진단)
---

# skill-doctor 리포트 조회

CLI 경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`
리포트 경로: `~/.claude/skill-doctor/reports/`

## 실행 절차

### 1. 리포트 목록 조회

리포트 디렉토리의 파일 목록을 조회:
```bash
ls -lt ~/.claude/skill-doctor/reports/ 2>/dev/null || echo "리포트가 없습니다."
```

사용자가 특정 스킬을 지정하면:
```bash
ls -lt ~/.claude/skill-doctor/reports/{스킬명}*.md 2>/dev/null || echo "해당 스킬의 리포트가 없습니다."
```

### 2. 리포트 표시

목록을 테이블로 보여주고 사용자가 선택하면 해당 파일을 Read 도구로 읽어서 표시.

```
## 📋 진단 리포트 목록

| # | 파일 | 날짜 | 스킬 |
|---|------|------|------|
| 1 | {filename} | {date} | {skill} |
```

### 3. 다음 단계 추천

리포트 내용에 따라 AskUserQuestion 도구로 다음 단계를 제안:

**리포트가 없는 경우:**
```yaml
questions:
  - question: '아직 진단 이력이 없습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'diagnose — 진단 실행'
        description: '스킬을 선택하여 진단을 시작합니다'
      - label: 'dashboard — 스킬 현황'
        description: '추적 중인 스킬 목록을 확인합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

**미적용 수정 제안이 있는 경우:**
```yaml
questions:
  - question: '이 리포트에 미적용 수정 제안이 있습니다. 어떻게 할까요?'
    header: '다음 단계'
    options:
      - label: 'heal {skill} — 수정 적용'
        description: '제안된 수정사항을 스킬에 적용합니다'
      - label: 'diagnose {skill} — 재진단'
        description: '최신 데이터로 다시 진단합니다'
      - label: 'dashboard — 전체 현황'
        description: '다른 스킬 상태도 확인합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

사용자 선택에 따라 해당 스킬을 실행한다.
