---
name: init
description: 프로젝트에 skill-doctor를 설정하고 시그널 자동 수집을 활성화할 때 사용 (skill-doctor 설정, init, 초기화, skill-doctor 시작, 셋업, skill-doctor 설치)
---

# skill-doctor 초기화

CLI 경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`

## 실행 절차

### 1. 데이터 디렉토리 초기화
```bash
mkdir -p ~/.claude/skill-doctor/{tmp,reports,active}
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py list
```
list 명령이 DB를 자동 생성한다. 에러 없으면 정상.

### 2. 마켓플레이스 스킬 발견
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py discover-marketplace
```
설치된 마켓플레이스 플러그인의 스킬을 자동으로 DB에 등록한다.

### 3. Hook 기반 시그널 수집 확인

skill-doctor는 **Hook + Agent 하이브리드** 방식으로 시그널을 자동 수집한다:

| 단계 | 동작 | 주체 |
|------|------|------|
| Phase 1 | 도구 실패, 사용자 메시지, 스킬명을 raw 이벤트로 누적 | Hook (시스템 레벨) |
| Phase 2 | Stop 시 raw 이벤트를 Claude 컨텍스트에 주입 | Hook → additionalContext |
| Phase 3 | 유의미한 시그널만 판별 + cause_type 귀속 → DB 기록 | Claude (agent) |

> **CLAUDE.md 시그널 기록 지침은 더 이상 필수가 아닙니다.** Hook이 raw 이벤트를 수집하고 Claude가 의미를 판단합니다.
> `redo`, `manual_fix`, `blocked`, `clarify`는 hook으로 감지하기 어려우므로 `/skill-doctor:record`로 수동 기록하거나, CLAUDE.md 지침으로 보조 수집합니다.

훅 동작 확인:
```bash
ls "${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json" && echo "훅 설정 존재"
python3 -c "import json; d=json.load(open('${CLAUDE_PLUGIN_ROOT}/hooks/hooks.json')); print(f'등록된 이벤트: {len(d.get(\"hooks\", {}))}개')"
```

### 4. (선택) CLAUDE.md 보조 시그널 지침 추가

hook으로 감지하기 어려운 시그널(`redo`, `manual_fix`, `clarify`, `blocked`)의 보조 수집을 원하면, 프로젝트의 `.claude/CLAUDE.md`에 아래 블록을 추가한다.

`<!-- skill-doctor -->` 마커가 이미 있으면 스킵.

마커가 없으면 파일 끝에 추가:

    <!-- skill-doctor -->
    ## skill-doctor 보조 시그널 기록

    hook이 자동 감지하지 못하는 이벤트(redo, manual_fix, clarify, blocked) 발생 시
    type+cause_type+cause_detail을 메모리에 누적한다.
    스킬 종료 시 누적된 시그널을 Write(~/.claude/skill-doctor/tmp/sd-session-{timestamp}.json)로 저장 후
    `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py record --file <path>`로 기록한다.

    **원인 귀속**: 스킬 결함 vs 사용자 측 요인 판단.
    - **스킬 측** (CD 가산): ambiguous_instruction, missing_precondition, scope_exceeded, error_handling, output_mismatch
    - **사용자 측** (CD 가산 안 함): insufficient_context, user_preference, external_issue
    <!-- /skill-doctor -->

### 5. 설치 확인 리포트

```
## skill-doctor 초기화 완료

| 항목 | 상태 |
|------|------|
| 데이터 디렉토리 | ✅ ~/.claude/skill-doctor/ |
| DB | ✅ skill-doctor.db |
| Hook+Agent 시그널 수집 | ✅ 자동 활성 (raw 이벤트 → Claude 판단 → DB) |
| CLAUDE.md 보조 | ⬜ 선택사항 (redo, manual_fix 보조 수집) |
| 플러그인 | ✅ skill-doctor@jake-plugins |

시그널 수집 방식:
- **자동 (Hook+Agent)**: Hook이 raw 이벤트 수집 → Claude가 의미 판단 + cause_type 귀속 → DB 기록
- **수동 (/skill-doctor:record)**: 모든 시그널 타입 — 가장 정확한 데이터
- **보조 (CLAUDE.md)**: redo, manual_fix, clarify, blocked — 선택적

사용 가능한 명령어:
- `/skill-doctor:dashboard` — 스킬 건강도 현황
- `/skill-doctor:diagnose <스킬명>` — 특정 스킬 진단
- `/skill-doctor:heal <스킬명>` — 자동 수정
```

### 6. 다음 단계 추천

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

## 시그널 기록

> **자동 수집 (Hook+Agent)**: 도구 실패, 사용자 메시지 등 raw 이벤트를 Hook이 수집하고, Stop 시 Claude가 유의미한 시그널만 판별하여 DB에 기록합니다.
> **수동 보조**: redo, manual_fix, clarify, blocked는 hook으로 감지하기 어려우므로, 발생 시 `/skill-doctor:record`로 수동 기록하면 데이터 품질이 향상됩니다.
