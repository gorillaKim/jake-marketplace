---
name: suggest
description: 반복 작업 패턴을 분석하여 새 스킬이나 에이전트 생성을 제안할 때 사용 (패턴 분석, 스킬 제안, suggest, 반복 작업, 자동화 제안, 스킬 만들까, 에이전트 제안)
---

# skill-doctor 자동화 제안 (suggest)

## 실행 절차

### 1. 분석 데이터 수집 (온디맨드)

DB 기반이 아닌 실시간 분석으로 반복 패턴을 감지한다:

**a) 최근 git 커밋 분석**
```bash
git log --oneline -30
```
커밋 메시지에서 반복되는 작업 패턴을 추출.

**b) 기존 스킬 사용 이력 확인**
```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py list --all-projects
```
이미 스킬로 존재하는 작업을 필터링.

**c) 프로젝트 구조 분석**
```bash
ls .claude/skills/ .claude/agents/ 2>/dev/null
```
현재 프로젝트에 어떤 스킬/에이전트가 있는지 파악.

**d) 사용자에게 추가 질문**

AskUserQuestion 도구로 구조화된 질문:
```yaml
questions:
  - question: '최근 반복적으로 수행하는 작업이 있나요?'
    header: '반복 패턴 수집'
    options:
      - label: '네, 있습니다'
        description: '반복 작업을 설명해주세요 (후속 질문에서 상세 입력)'
      - label: '자동 분석 결과만 확인'
        description: 'git 커밋과 기존 스킬 분석 결과만 봅니다'
    multiSelect: false
```

### 2. 패턴 분류

발견된 패턴을 아래 기준으로 분류:

| 형태 | 기준 | 예시 |
|------|------|------|
| **스킬** | 단일 작업, 정해진 절차, 사용자가 직접 트리거 | CSV 파싱 → 이벤트 정의 생성 |
| **서브에이전트** | 다른 스킬에서 호출되는 전문화된 역할 | 코드 분석기, 검증기 |
| **팀에이전트** | 여러 에이전트 협업이 필요한 파이프라인 | 분석 → 구현 → 검증 |
| **규칙** | 항상 적용되는 코딩 컨벤션/패턴 | 네이밍 규칙, 에러 핸들링 |

### 3. 제안 리포트

```
## 자동화 제안

### 발견된 패턴 ({count}건)

1. **{pattern_name}** — {description}
   - 반복 빈도: 약 {n}회
   - 권장 형태: {스킬/에이전트/팀/규칙}
   - 이유: {why}

### 다음 단계
- 생성하려면 `/skill-doctor:create {pattern_name}` 사용
- 무시하려면 "건너뛰기" 선택
```

### 4. 다음 단계 추천

제안 결과에 따라 AskUserQuestion 도구로 다음 단계를 제안:

**제안이 있는 경우:**
```yaml
questions:
  - question: '위 제안 중 생성할 항목을 선택해주세요.'
    header: '다음 단계'
    options:
      # 발견된 패턴을 동적으로 옵션화
      - label: 'create {pattern_1} — {type}'
        description: '{pattern_1_description}'
      - label: 'create {pattern_2} — {type}'
        description: '{pattern_2_description}'
      - label: '모두 건너뛰기'
        description: '제안을 저장만 하고 나중에 처리합니다'
    multiSelect: true
```

**제안이 없는 경우:**
```yaml
questions:
  - question: '특별한 반복 패턴이 발견되지 않았습니다. 다음으로 무엇을 할까요?'
    header: '다음 단계'
    options:
      - label: 'dashboard — 스킬 현황'
        description: '기존 스킬 건강도를 확인합니다'
      - label: 'create — 직접 생성'
        description: '수동으로 새 스킬/에이전트를 생성합니다'
      - label: '종료'
        description: '여기서 마칩니다'
    multiSelect: false
```

사용자 선택에 따라 해당 스킬을 실행한다. 제안 이력은 `~/.claude/skill-doctor/reports/suggest-{timestamp}.md`에 저장.
