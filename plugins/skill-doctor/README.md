# skill-doctor

스킬 실행 중 발생하는 문제를 **자동으로 감지**하고, **스스로 개선**하는 플러그인.
에러, 사용자 수정, 재시도 등의 시그널을 세션마다 수집하여 반복 문제를 진단하고, 스킬 프롬프트를 자동 수정합니다.

## 설치

```bash
/plugin marketplace add gorillaProject/jake-marketplace
/plugin install skill-doctor@jake-plugins
```

초기 설정:

```
/skill-doctor:init
```

---

## 작동 원리

### 전체 파이프라인

```
┌─────────────────────────────────────────────────────────────────────┐
│  스킬 실행 중                                                        │
│                                                                     │
│  1. Hook이 raw 이벤트 자동 수집 (tool 에러, 사용자 메시지)              │
│  2. 스킬 완료 시 Claude가 "스킬 품질 문제인지" 판단하여 시그널 기록       │
│  3. cd_score ≥ 30 → 자동으로 diagnose 실행                           │
│  4. 같은 문제 3회 반복 → 자동으로 heal 제안                            │
│  5. heal 적용 후 3세션 경과 → 자동으로 성공/실패 판정                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 시그널 수집: 2단계 하이브리드

시그널 수집은 **Hook(객관적 감지)**과 **Claude(주관적 판단)** 두 레이어로 동작합니다.

#### Layer 1: Hook이 자동 수집 (기계적)

| 감지 대상 | Hook 이벤트 | 감지 조건 |
|-----------|------------|-----------|
| tool 에러 (hard) | `PostToolUseFailure` | tool 실행 실패 (exit code ≠ 0) |
| tool 에러 (soft) | `PostToolUse` | 성공했지만 stdout에 error/exception 패턴 |
| 사용자 인터럽트 | `PostToolUseFailure` | `is_interrupt: true` |
| 사용자 메시지 | `UserPromptSubmit` | 3자 이상의 사용자 입력 |

> Hook은 **분류 없이 원본 그대로** 누적만 합니다.

#### Layer 2: Claude가 판단 (의미 분류)

스킬 완료 시 누적된 raw 이벤트를 Claude에게 전달. Claude가 **스킬 품질 문제인지** 판단합니다.

| 시그널 type | Claude 판단 기준 | 예시 |
|-------------|-----------------|------|
| `tool_error` | 스킬 프롬프트가 잘못된 명령을 지시 | 없는 CLI 도구 호출 |
| `correct` | 사용자가 스킬 동작을 교정 | "그게 아니라 이렇게 해" |
| `redo` | 같은 작업을 다시 해야 함 | 결과물 잘못되어 재실행 |
| `cancelled` | 사용자가 스킬 취소 | 중도 인터럽트 |
| `manual_fix` | 사용자가 결과를 직접 수정 | "내가 직접 고칠게" |
| `clarify` | 스킬이 추가 질문 필요 | 모호한 지시로 되물음 |
| `blocked` | 정당한 중단 | 권한 부족 등 |

**Claude의 필터링 규칙:**
- grep 결과 없음 등 정상 탐색 → 무시
- 단순 대화/질문 → 무시
- 스킬 프롬프트의 결함이 원인인 것만 → 시그널로 기록
- 유의미한 시그널 없으면 → 아무것도 안 함

> **요약: Hook은 "무엇이 일어났는지", Claude는 "그게 스킬의 문제인지"를 담당합니다.**

### 자동 체이닝

시그널 기록 후 다음 단계가 자동으로 트리거됩니다:

```
스킬 완료 → 시그널 기록(record)
                │
                ├── cd_score < 30 → 종료 (문제 없음)
                │
                └── cd_score ≥ 30 → 자동 diagnose
                                        │
                                        ├── escalation < 3 → 리포트만 저장
                                        │
                                        └── escalation ≥ 3 + 로컬 스킬 → 자동 heal 제안
                                                                            │
                                                                            └── 사용자 승인 → 적용
                                                                                    │
                                                                                    └── 3세션 후 자동 검증
                                                                                          ├── 재발 없음 → ✅ 확정
                                                                                          └── 재발 → ❌ 실패 → 다른 접근 시도
```

---

## 평가 기준

### 1. CD Score (세션 단위)

스킬 실행 1회에 대한 즉시 점수. **높을수록 문제가 심각.**

| type | 점수 | 의미 |
|------|------|------|
| `clarify` | 0 | 질문 — 정상 |
| `blocked` | 0 | 정당한 중단 |
| `tool_error` | +15 | 도구 실패 |
| `correct` | +25 | 사용자가 교정 |
| `manual_fix` | +30 | 수동 우회 |
| `redo` | +40 | 재시도 필요 |
| `cancelled` | +50 | 스킬 취소 |

> **사용자 측 원인**(`insufficient_context`, `user_preference`, `external_issue`)이면 **점수 0** — 스킬 결함이 아닌 상황이 건강도를 낮추지 않습니다.

### 2. 원인 귀속 (Cause Attribution)

시그널 기록 시 **스킬 결함 vs 사용자 측 요인**을 구분합니다.

**스킬 측** (CD 가산, 에스컬레이션 대상):

| cause_type | 설명 |
|---|---|
| `ambiguous_instruction` | 스킬 프롬프트의 지시가 모호 |
| `missing_precondition` | 전제조건 미검증 |
| `scope_exceeded` | 범위 정의 불명확 |
| `error_handling` | 예외 상황 미처리 |
| `output_mismatch` | 결과물이 기대와 다름 |

**사용자 측** (CD 가산 안 함, 에스컬레이션 제외):

| cause_type | 설명 |
|---|---|
| `insufficient_context` | 사용자가 충분한 정보를 안 줌 |
| `user_preference` | 사용자 취향 차이 |
| `external_issue` | 외부 환경 문제 (네트워크, 권한 등) |

> **판단 기준**: 같은 상황에서 스킬이 일관되게 잘못 판단 → 스킬 결함. 사용자가 정보를 안 줬거나 취향 차이 → 사용자 측.

### 3. Escalation Level (크로스 세션)

동일 cause_type이 **별개 세션에서 반복**된 횟수로 결정. CLI가 자동 계산합니다.

| 반복 횟수 | Level | 자동 액션 |
|-----------|-------|-----------|
| 1회 | 1 | 프로파일 업데이트만 |
| 2회 | 2 | 진단 리포트 생성 |
| **3회** | **3** | **heal diff 제안** |
| 4회+ | 4 | 자동 적용 추천 |

### 4. Health Score (스킬 건강도)

```
health_score = max(0, 100
    - (미해결 스킬측 cause_type 수 × 15)
    - (최근 3세션 평균 CD ÷ 3)
    - (구조 이슈 × 5, 최대 -20))
```

| 감점 요인 | 감점 |
|-----------|------|
| 미해결 스킬측 cause_type 1개당 | -15 |
| 최근 3세션 평균 CD ÷ 3 | 가변 |
| SKILL.md 구조 이슈 (frontmatter 누락 등) | -5 (최대 -20) |
| 사용자 측 cause_type | 0 |

### 5. Heal 검증 (자동)

heal 적용 후 자동으로 성공/실패를 판정합니다.

| 조건 | 판정 | 액션 |
|------|------|------|
| heal 후 같은 cause_type 재발 | **실패** | resolved에서 제거, 다른 접근 시도 |
| 3세션 경과 + 재발 없음 | **확정** | heal 성공으로 확정 |

---

## 사용 가능한 명령어

| 명령어 | 설명 |
|---|---|
| `/skill-doctor:init` | 프로젝트 초기 설정 (DB, 환경 점검) |
| `/skill-doctor:dashboard` | 전체 스킬 건강도 현황 |
| `/skill-doctor:diagnose` | 스킬 진단 및 리포트 생성 |
| `/skill-doctor:heal` | 진단된 문제를 스킬 프롬프트에 자동 수정 |
| `/skill-doctor:record` | 시그널 수동 기록 |
| `/skill-doctor:report` | 과거 진단 리포트 조회 |
| `/skill-doctor:suggest` | 반복 패턴 분석 → 새 스킬/에이전트 제안 |
| `/skill-doctor:create` | 새 스킬/에이전트/규칙 생성 |
| `/skill-doctor:checkup` | skill-doctor 자체 환경 점검 및 자동 수정 |

### 스킬 플로우

```
init ──→ dashboard / suggest
           │
dashboard ─┤──→ diagnose (문제 있는 스킬)
           └──→ suggest (새 스킬 제안)
                  │
diagnose ─────┤──→ heal (로컬 스킬, level 3+)
              ├──→ suggest (마켓플레이스 스킬)
              └──→ report
                     │
heal ─────────┤──→ dashboard
              └──→ diagnose (다른 스킬)

record ───────┤──→ diagnose (CD 높을 때)
              └──→ dashboard
```

### 마켓플레이스 스킬 지원

설치된 마켓플레이스 플러그인의 스킬을 자동 발견하여 추적합니다.

| 기능 | 로컬 스킬 | 마켓플레이스 스킬 |
|------|-----------|-----------------|
| 시그널 수집 | ✅ | ✅ |
| 진단 (diagnose) | ✅ | ✅ |
| 치유 (heal) | ✅ | ❌ (외부 플러그인) |
| 대안 | — | suggest로 개선된 로컬 버전 생성 |

---

## CLI

경로: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/cli.py`

| 명령어 | 용도 |
|---|---|
| `record --file <path>` | 세션 시그널 DB 기록. CD 점수 자동 계산. |
| `list [--all-projects]` | 추적 중인 스킬 목록 + health_score |
| `diagnose --skill <name> [--session <id>] [--full]` | 진단 데이터 JSON (escalation_level, auto_heal_actions 포함) |
| `discover-marketplace [--prune]` | 마켓플레이스 스킬 자동 발견 |
| `update-profile --skill <name> --health-score <N> [...]` | 프로파일 업데이트 |

상세: [docs/CLI_REFERENCE.md](docs/CLI_REFERENCE.md)

---

## 데이터 저장

| 항목 | 경로 | 비고 |
|---|---|---|
| DB | `~/.claude/skill-doctor/skill-doctor.db` | 재설치해도 유지 |
| 리포트 | `~/.claude/skill-doctor/reports/` | 90일 후 자동 삭제 |
| 임시 파일 | `~/.claude/skill-doctor/tmp/` | record 후 자동 삭제 |
| 활성 세션 | `~/.claude/skill-doctor/active/` | 스킬 실행 중 시그널 누적 |

---

## 플러그인 구조

```
plugins/skill-doctor/
├── agents/
│   ├── skill-doctor.md          ← 진단 에이전트 (haiku)
│   └── skill-healer.md          ← 셀프힐링 에이전트 (sonnet)
├── skills/
│   ├── init/          dashboard/     diagnose/
│   ├── heal/          record/        report/
│   ├── suggest/       create/        checkup/
├── hooks/
│   └── hooks.json               ← 시그널 자동 수집 (6개 이벤트)
├── scripts/
│   ├── cli.py                   ← CLI (python3, 외부 의존성 없음)
│   └── signal-collector.py      ← Hook → 시그널 변환 + 자동 체이닝
└── docs/
    ├── CLI_REFERENCE.md
    ├── CREATION_GUIDE.md
    └── SIGNAL_GUIDE.md
```

## 요구사항

- python3 (macOS 기본 포함)
- 외부 패키지 불필요
