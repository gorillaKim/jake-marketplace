---
name: create
description: 새 스킬, 에이전트, 규칙을 표준 명세에 맞춰 생성할 때 사용 (스킬 생성, 에이전트 생성, create, 스킬 만들어, 새 스킬, 스캐폴딩, 규칙 생성)
---

# skill-doctor 생성 (create)

CLI 경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`
표준 명세 가이드: `${CLAUDE_PLUGIN_ROOT}/docs/CREATION_GUIDE.md`

## 실행 절차

### 1. 생성 대상 결정

suggest에서 연결된 경우 이미 정보가 있으므로 확인만.
그 외에는 AskUserQuestion 도구로 구조화된 질문:

**생성 타입 선택:**
```yaml
questions:
  - question: '무엇을 만들까요?'
    header: '생성 대상'
    options:
      - label: '스킬'
        description: '사용자가 직접 트리거하는 자동화 작업 (예: /commit, /deploy)'
      - label: '에이전트'
        description: '다른 스킬에서 호출되는 전문화된 역할 (예: 코드 분석기)'
      - label: '규칙'
        description: '항상 적용되는 코딩 컨벤션/패턴 (예: 네이밍 규칙)'
    multiSelect: false
```

**위치 선택:**
```yaml
questions:
  - question: '어디에 생성할까요?'
    header: '생성 위치'
    options:
      - label: '프로젝트 (.claude/)'
        description: '이 프로젝트에서만 사용 (팀원과 공유 가능)'
      - label: '사용자 (~/.claude/)'
        description: '모든 프로젝트에서 개인적으로 사용'
      - label: '플러그인'
        description: '플러그인으로 배포 (재설치 필요)'
    multiSelect: false
```

이름과 목적은 자유 텍스트로 추가 질문. kebab-case로 정규화.

### 2. 가이드 참조

반드시 `${CLAUDE_PLUGIN_ROOT}/docs/CREATION_GUIDE.md`를 Read 도구로 읽고 해당 타입의 명세를 따른다.

### 3. 스캐폴딩

#### 스킬 생성 시
```
{location}/skills/{name}/
└── SKILL.md
```

SKILL.md 필수 구조 (아래 요소를 모두 포함):

- **frontmatter**: name, description (트리거 키워드 괄호 포함)
- **CLI 경로 헤더**: `CLI 경로: python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`
- **## 실행 절차**: `### 1.`, `### 2.` 등 번호 정리, CLI 명령은 코드블록
- **## 시그널 기록**: 이벤트 누적 → tmp JSON 저장 → `cli.py record` → cd_score ≥ 50이면 diagnose
- **다음 단계 추천**: AskUserQuestion으로 후속 액션 제안

> **필수**: 모든 새 스킬에 위 "시그널 기록" 섹션을 포함한다. 이 섹션이 없으면 시그널이 수집되지 않아 skill-doctor의 셀프힐링이 작동하지 않는다.

체크리스트 (CREATION_GUIDE.md 섹션 5 참조):
- [ ] name: 소문자+하이픈, 최대 64자
- [ ] description: 트리거 키워드 괄호 포함
- [ ] 절차: 번호 매기기로 명확하게
- [ ] CLI 명령어: 코드 블록으로 감싸기
- [ ] **시그널 기록 섹션 포함** (셀프힐링 필수)

#### 에이전트 생성 시
```
{location}/agents/{name}.md
```

구조:
```markdown
---
name: {name}
description: {언제 이 에이전트에 위임해야 하는지}
model: {haiku|sonnet|opus}
tools:
  - {필요한 도구만}
---

# {제목}

{시스템 프롬프트}
```

체크리스트:
- [ ] name, description: **필수**
- [ ] tools: 최소 권한 원칙
- [ ] model: 작업 복잡도에 맞게
- [ ] 플러그인 에이전트는 hooks, mcpServers, permissionMode 사용 불가

#### 규칙 생성 시
```
{location}/rules/{name}.md
```

구조:
```markdown
---
paths:          # 선택: 특정 파일에서만 적용할 때
  - "src/**/*.ts"
---

# {규칙 제목}

{규칙 내용 — 간결하게}
```

### 4. 사용자 리뷰

생성된 파일 내용을 사용자에게 표시하고 수정할 부분이 있는지 확인.
수정 요청이 있으면 반영 후 다시 표시.

### 5. 파일 생성

승인 후 Write 도구로 파일 생성.

플러그인에 생성한 경우:
```
플러그인 재설치가 필요합니다:
claude plugin uninstall {plugin-name} && claude plugin install {plugin-name}@{registry}
```

### 6. 다음 단계 추천

AskUserQuestion 도구로 다음 단계를 제안:

```yaml
questions:
  - question: '{name} 생성이 완료되었습니다. 시그널 자동 기록이 활성화됩니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: '바로 테스트 실행'
        description: '생성한 스킬/에이전트를 바로 실행해봅니다'
      - label: 'create — 추가 생성'
        description: '다른 스킬/에이전트/규칙도 생성합니다'
      - label: 'dashboard — 현황 확인'
        description: '전체 스킬 건강도를 확인합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

사용자 선택에 따라 해당 스킬을 실행한다.

## 시그널 기록

> **자동 수집 (Hook+Agent)**: 도구 실패, 사용자 메시지 등 raw 이벤트를 Hook이 수집하고, Stop 시 Claude가 유의미한 시그널만 판별하여 DB에 기록합니다.
> **수동 보조**: redo, manual_fix, clarify, blocked는 hook으로 감지하기 어려우므로, 발생 시 `/skill-doctor:record`로 수동 기록하면 데이터 품질이 향상됩니다.
