# skill-doctor

스킬 실행 중 발생하는 문제(모호성, 전제조건 누락, 스코프 불일치 등)를 **여러 세션에 걸쳐 자동으로 감지**하고, **점진적으로 스킬을 개선**하는 플러그인.

## 설치

```bash
/plugin marketplace add gorillaProject/jake-marketplace
/plugin install skill-doctor@jake-plugins
```

## 사용법

### 자동 시그널 수집

`/skill-doctor:init`으로 프로젝트 CLAUDE.md에 시그널 기록 지침을 추가하면, 모든 스킬 실행 중 시그널이 자동으로 수집됩니다.

```
스킬 실행 중 이벤트 발생 → 메모리에 누적
  ↓
스킬 종료 → cli.py record
  ↓
CD ≥ 50 → cli.py diagnose → skill-doctor 서브에이전트 → 리포트
```

> skill-doctor 자체(`/skill-doctor:diagnose`) 실행 시에는 시그널을 수집하지 않습니다.

### 사용 가능한 명령어

| 명령어 | 설명 |
|---|---|
| `/skill-doctor:init` | 프로젝트 초기 설정 (DB, CLAUDE.md) |
| `/skill-doctor:dashboard` | 전체 스킬 건강도 현황 |
| `/skill-doctor:diagnose [스킬명]` | 스킬 진단 및 리포트 생성 |
| `/skill-doctor:heal [스킬명]` | 진단된 문제를 스킬 프롬프트에 자동 수정 |
| `/skill-doctor:record` | 시그널 수동 기록 |
| `/skill-doctor:report` | 과거 진단 리포트 조회 |
| `/skill-doctor:suggest` | 반복 패턴 분석 → 새 스킬/에이전트 제안 |
| `/skill-doctor:create` | 새 스킬/에이전트/규칙 생성 |

각 스킬은 종료 시 AskUserQuestion으로 다음 단계를 추천합니다.

---

## 핵심 개념

### CD(Clarification Debt) 점수

스킬 실행 중 이벤트에 점수를 부여. **50 이상이면 진단 트리거.**

| 이벤트 | 점수 | 감지 | 비고 |
|---|---|---|---|
| `clarify` | **+0** | 확실 | 정상 동작 (질문은 올바른 행동) |
| `correct` | +25 | best effort | |
| `redo` | +40 | 확실 | |
| `tool_error` | +15 | 확실 | |
| `cancelled` | +50 | 확실 | |
| `manual_fix` | +30 | best effort | |
| `blocked` | +0 | 확실 | 올바르게 멈춤 |

> **사용자 측 원인(`insufficient_context`, `user_preference`, `external_issue`)은 CD에 가산되지 않으며 에스컬레이션에서 제외됩니다.** 스킬 결함이 아닌 상황이 스킬 건강도를 낮추지 않도록 합니다.

### 원인 귀속 (Attribution)

시그널 기록 시 **스킬 결함 vs 사용자 측 요인**을 구분합니다. 사용자 측 원인은 스킬 건강도에 영향을 주지 않습니다.

**스킬 측 원인** (CD 가산, 에스컬레이션 대상):

| cause_type | 설명 |
|---|---|
| `ambiguous_instruction` | 스킬 프롬프트의 지시가 모호 |
| `missing_precondition` | 스킬이 전제조건을 검증하지 않음 |
| `scope_exceeded` | 스킬 범위 정의가 불명확 |
| `error_handling` | 예외 상황 미처리 |
| `output_mismatch` | 결과물 포맷/품질이 기대와 다름 |

**사용자 측 원인** (CD 가산 안 함, 에스컬레이션 제외):

| cause_type | 설명 |
|---|---|
| `insufficient_context` | 사용자가 충분한 정보를 제공하지 않음 |
| `user_preference` | 사용자 개인 선호에 의한 수정 (스킬 기본 동작은 정상) |
| `external_issue` | 외부 환경 문제 (네트워크, 권한, 파일 부재 등) |

**판단 기준**: 같은 상황에서 스킬이 일관되게 잘못 판단 → 스킬 결함. 사용자가 정보를 안 줬거나 취향 차이 → 사용자 측.

### 점진적 에스컬레이션

**스킬 측 cause_type**의 같은 문제가 반복될수록 대응 수준이 올라감:

| 반복 | level | 행동 |
|---|---|---|
| 1회 | 1 | 프로파일 업데이트만 |
| 2회 | 2 | 진단 리포트 → 사용자 알림 |
| 3회 | 3 | 스킬 파일 수정 diff 제안 |
| 4회+ | 4 | 자동 적용 추천 |

> 사용자 측 cause_type은 반복 횟수에 포함되지 않습니다.

### health_score

```
health_score = max(0, 100 - (미해결_스킬측_cause_type수 × 15) - (avg_cd_last_3 ÷ 3) - (구조_이슈수 × 5))
```

> - 사용자 측 cause_type은 health_score에 영향 없음
> - 구조 이슈(frontmatter 누락, 시그널 기록 섹션 없음 등)는 건당 -5점 (최대 -20점)

### 스킬 플로우

각 스킬은 종료 시 AskUserQuestion으로 상황에 맞는 다음 단계를 추천합니다:

```
init → dashboard / suggest
dashboard → diagnose / heal / suggest (상황별)
diagnose → heal / report / dashboard
heal → dashboard / diagnose(다른 스킬) / report
record → diagnose(CD 높을 때) / dashboard
report → heal / diagnose / dashboard
suggest → create(선택적) / dashboard
create → 테스트 실행 / create(추가) / dashboard
```

---

## CLI

경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`

| 명령어 | 용도 |
|---|---|
| `record --file <path>` | 세션 시그널 DB 기록. CD 점수 자동 계산. 입력 파일 자동 삭제. |
| `list [--all-projects]` | 기록된 스킬 목록 + health_score |
| `diagnose --skill <name> [--session <id>] [--full] [--all-projects]` | 진단 데이터 JSON 출력 |
| `update-profile --skill <name> --health-score <N> [--resolve <cause_type>] [--dismiss <cause_type>] [--heal-tracking <json>] [--fail-heal <id>] [--confirm-heal <id>]` | 프로파일 업데이트 |

### 예시

```bash
# 스킬 목록
python3 .../cli.py list

# 진단 (최근 세션 자동 선택)
python3 .../cli.py diagnose --skill e2e-testid

# 이슈 해결 처리
python3 .../cli.py update-profile --skill e2e-testid --health-score 85 --resolve ambiguous_instruction

# 제안 거부 (30일간 재제안 안 함)
python3 .../cli.py update-profile --skill e2e-testid --health-score 72 --dismiss scope_exceeded
```

상세: [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)

---

## 데이터 저장

| 항목 | 경로 | 비고 |
|---|---|---|
| DB | `~/.claude/skill-doctor/skill-doctor.db` | 플러그인 재설치해도 유지 |
| 리포트 | `~/.claude/skill-doctor/reports/` | 90일 후 자동 삭제 |
| 임시 파일 | `~/.claude/skill-doctor/tmp/` | record 후 자동 삭제 |

데이터는 `~/.claude/skill-doctor/`에 저장. 플러그인 업데이트/재설치 시에도 유지.

---

## 플러그인 구조

```
plugins/skill-doctor/
├── .claude-plugin/
│   └── plugin.json              ← 플러그인 메타데이터
├── agents/
│   ├── skill-doctor.md          ← 진단 서브에이전트 (haiku)
│   └── skill-healer.md          ← 셀프힐링 서브에이전트 (sonnet)
├── skills/
│   ├── init/SKILL.md            ← /skill-doctor:init
│   ├── dashboard/SKILL.md       ← /skill-doctor:dashboard
│   ├── diagnose/SKILL.md        ← /skill-doctor:diagnose
│   ├── heal/SKILL.md            ← /skill-doctor:heal
│   ├── record/SKILL.md          ← /skill-doctor:record
│   ├── report/SKILL.md          ← /skill-doctor:report
│   ├── suggest/SKILL.md         ← /skill-doctor:suggest
│   └── create/SKILL.md          ← /skill-doctor:create
├── scripts/
│   └── cli.py                   ← CLI (python3, 외부 의존성 없음)
├── docs/
│   ├── CLI_REFERENCE.md         ← CLI 상세 사용법
│   ├── CREATION_GUIDE.md        ← 스킬/에이전트/규칙 생성 가이드
│   ├── SIGNAL_GUIDE.md          ← 시그널 기록 레퍼런스
│   └── signal-recording.md      ← 시그널 수집 규칙 문서
└── README.md
```

## 요구사항

- python3 (macOS 기본 포함)
- 외부 패키지 불필요

## 향후 확장

- **Flow B**: 일반 대화에서 반복 패턴 감지 → 새 스킬 생성 제안
- **가중치**: 같은 에러 반복 ×1.5 등 modifier
- **cli.py discover**: 대화 패턴 분석 서브커맨드
- **Cross-learning**: 스킬 A에서 발견된 패턴을 유사한 스킬 B에도 선제적으로 적용 제안
