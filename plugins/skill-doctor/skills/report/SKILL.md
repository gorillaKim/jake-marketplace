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
python3 -c "
import json, pathlib
reports_dir = pathlib.Path.home() / '.claude/skill-doctor/reports'
if not reports_dir.exists():
    print(json.dumps({'reports': [], 'message': '리포트가 없습니다.'}))
else:
    files = sorted(reports_dir.glob('*.md'), key=lambda f: f.stat().st_mtime, reverse=True)
    print(json.dumps({'reports': [{'name': f.name, 'size': f.stat().st_size, 'mtime': f.stat().st_mtime} for f in files]}, ensure_ascii=False))
"
```

사용자가 특정 스킬을 지정하면 해당 스킬명으로 필터링하여 조회.

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

**리포트에 level 3+ 이슈가 포함된 경우 (리포트 내용에 "heal 실행을 권장" 또는 "자동 적용 추천" 텍스트가 포함됨):**
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

**리포트가 있고 특별한 조치가 필요 없는 경우:**
```yaml
questions:
  - question: '리포트를 확인했습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'diagnose — 최신 진단'
        description: '최신 데이터로 스킬을 진단합니다'
      - label: 'dashboard — 전체 현황'
        description: '스킬 건강도를 확인합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

사용자 선택에 따라 해당 스킬을 실행한다.

## 시그널 기록

> **자동 수집 (Hook+Agent)**: 도구 실패, 사용자 메시지 등 raw 이벤트를 Hook이 수집하고, Stop 시 Claude가 유의미한 시그널만 판별하여 DB에 기록합니다.
> **수동 보조**: redo, manual_fix, clarify, blocked는 hook으로 감지하기 어려우므로, 발생 시 `/skill-doctor:record`로 수동 기록하면 데이터 품질이 향상됩니다.
