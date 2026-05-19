# Sprint Retro — engram 만들기 (중간 회고)

> 기간: 미설정 (스프린트 진행 중)
> 스프린트 목표: engram 완성하기
> 생성일: 2026-05-19
> 생성: engram-retro@test-scenario
> 유형: **중간 회고** (스프린트 status=active, 아직 종료되지 않음)

---

## 1. 스프린트 요약

| 항목 | 수치 |
|------|------|
| 전체 이슈 | 4 |
| 완료 (finished) | 0 |
| 사용자 검토 대기 (demo) | 4 |
| 미완료 (working/ready/required) | 0 |
| 취소 (cancelled) | 0 |
| 완료율 | 0% (전원 demo — 사용자 최종 승인 대기) |

> 참고: 모든 이슈가 demo 상태입니다. 구현은 완료되었으나 리뷰 사이클이 진행 중이며,
> 일부 이슈는 CHANGES_REQUESTED caveat 로 인해 재작업이 필요한 상태입니다.

---

## 2. 완료된 것 (Done)

현재 스프린트 기준 `finished` 이슈 없음. 전원 `demo` 상태.

### demo 상태 이슈 (구현 완료, 사용자 검토 대기)

| 이슈 | 에픽 | 우선순위 | demo 진입 시각 | 리뷰 결과 |
|------|------|----------|---------------|-----------|
| #24 engram-reviewer 에이전트 + review-issue 스킬 작성 | Epic #6 | high | 2026-05-19 06:15:58 | CHANGES_REQUESTED (2회) |
| #25 engram-retro 에이전트 + sprint-retro 스킬 작성 | Epic #6 | high | 2026-05-19 06:10:23 | CHANGES_REQUESTED (1회) |
| #26 README 업데이트 v0.5.0 — Agents/Skills 섹션 반영 | Epic #6 | medium | 2026-05-19 06:08:15 | 리뷰 미진행 |
| #35 engram-orchestrator:onboard 스킬 작성 | Epic #6 | high | 2026-05-19 06:10:24 | CHANGES_REQUESTED (1회) |

### 이슈별 태스크 완료 현황

**이슈 #24 — engram-reviewer 에이전트 + review-issue 스킬 작성**
- task #64: engram-reviewer.md 에이전트 파일 작성 — finished
- task #65: skills/review-issue/SKILL.md 작성 — finished

**이슈 #25 — engram-retro 에이전트 + sprint-retro 스킬 작성**
- task #66: engram-retro.md 에이전트 파일 작성 — finished
- task #67: skills/sprint-retro/SKILL.md 작성 — finished

**이슈 #26 — README 업데이트 v0.5.0**
- task #68: README Agents/Skills 섹션 + 플로우 다이어그램 업데이트 (v0.5.0) — required (미착수)

**이슈 #35 — engram-orchestrator:onboard 스킬 작성**
- task #92: skills/onboard/SKILL.md 작성 — frontmatter + 5-Step 트리거 진입점 — finished
- task #93: Step 1-2 구현 — 환경 체크 + 플랫폼별 CLI 설치 — finished
- task #94: Step 3 구현 — Desktop 앱 DMG 설치 — finished
- task #95: Step 4 구현 — MCP 등록 — finished
- task #96: Step 5 구현 — 연결 검증 + 실패 처리 — finished

---

## 3. 미완료 (Not Done)

`working` / `ready` / `required` 상태 이슈 없음.

단, 아래 태스크가 `required` 상태로 미착수:

| 태스크 | 이슈 | 상태 | 비고 |
|--------|------|------|------|
| task #68: README v0.5.0 업데이트 | #26 | required | 이슈 자체는 demo이나 실제 태스크 미착수 — 이슈 상태와 불일치 |

---

## 4. 주요 결정 (Decisions)

이슈 레벨 decision 노트는 없음. Epic #6 스코프의 project-wide decision이 다수 존재:

| 노트 | 요약 | 핵심 내용 |
|------|------|-----------|
| note #93 | MCP 연결 실패 처리 | 3단계: 서버 시작 안내 → 1회 재시도 → CLI fallback 여부 질문. 적용 범위: 모든 engram 에이전트/스킬 |
| note #94 | CLI 설치 방법 결정 | GitHub Releases 직접 활용. 플러그인 리포에 바이너리 미포함. 최신 버전 자동 설치 가능 |
| note #97 | Homebrew 우선 설치 결정 | 1순위 Homebrew (`brew tap gorillaKim/engram`), 2순위 tar.gz, 3순위 cargo |

---

## 5. 발견·배운 것 (Discoveries)

이슈 레벨 discovery 노트 없음.

### 스프린트 진행 과정에서 드러난 발견

- **태스크 상태와 실제 구현 불일치 패턴**: 이슈 #24, #25, #35 모두 1차 리뷰에서 "task 상태가 required인데 context note에는 완료라고 기재"된 불일치가 발견되어 CHANGES_REQUESTED 처리됨. 이는 워커 에이전트가 구현 파일은 작성했으나 태스크 상태 전이를 누락한 것으로, 2차 정리 후 resolved.

- **설계 변경이 구현 후 적용된 케이스**: 이슈 #24(reviewer)는 1차 구현 완료 후 note #92로 설계 변경(transition_to ready→working, 스코프 확장)이 적용되어 재작업 필요. 설계 확정 전 구현 시작의 위험성 확인.

- **engram GitHub Releases 에셋 구조 확인**: DMG(Desktop) vs tar.gz(CLI)가 별개 설치 대상임을 note #96에서 명확히 정리. 이전 note들(#95, #96, #97)이 상호 수정되며 최종 확정안(note #98)이 도출된 반복 개선 패턴 관찰.

---

## 6. 블로커 분석 (Blockers)

### 발생한 블로커

직접적인 blocker_detail 노트는 기록되지 않음.

단, 이슈 의존성으로 인한 실질적 블로킹:

| 피블로킹 이슈 | 블로킹 원인 | 해소 여부 |
|--------------|------------|---------|
| #26 README 업데이트 | "#24(reviewer), #25(retro) 완료 후 작업" 명시 — 선행 이슈 demo 상태 진입 후 착수 가능 | 부분 해소 (#24, #25 demo 진입. 단 #24 CHANGES_REQUESTED 잔존) |

### 블로킹 빈도 순위

| 이슈 | 블로킹 횟수 | 해소 여부 |
|------|------------|---------|
| #24 engram-reviewer | 1 (#26 블로킹) | 부분 해소 (demo 재진입, 미해결 caveat 잔존) |
| #25 engram-retro | 1 (#26 블로킹) | 해소 (demo 재진입 완료) |

---

## 7. 반복 주의사항 (Recurring Caveats)

### 2회 이상 등장한 패턴

**패턴 A — "태스크 상태 미갱신" (3건)**

| 이슈 | 노트 | 내용 |
|------|------|------|
| #24 | note #102 | task #64, #65 required 상태 미갱신 (1차 리뷰) |
| #25 | note #103 | task #66, #67 required 상태 미갱신 |
| #35 | note #104 | task #92~#96 총 5건 required 상태 미갱신 |

워커 에이전트가 파일 구현 완료 후 태스크 상태를 finished로 전이하지 않고 demo를 진행. 3건 모두 동일 패턴으로 1차 리뷰에서 CHANGES_REQUESTED 처리됨.

**패턴 B — "설계 미확정 상태의 구현 시작" (1건, 단일 이슈에서 복합 발생)**

| 이슈 | 노트 | 내용 |
|------|------|------|
| #24 | note #92 | transition_to="ready" → "working" 설계 변경 미반영 |
| #24 | note #106 | 동일 문제 재발 — 2차 리뷰에서도 CHANGES_REQUESTED |

이슈 #24는 1차 구현 → 1차 리뷰 CHANGES_REQUESTED → 정리 후 재demo → 2차 리뷰에서도 note #92 변경 미반영으로 재차 CHANGES_REQUESTED. 동일 설계 변경 사항이 2회 연속 반영되지 않음.

### Epic 스코프 미해결 Caveat (project-wide)

| 노트 | 요약 |
|------|------|
| note #95 | macOS Gatekeeper: DMG 설치 후 xattr -cr 필수 |
| note #98 | CLI 설치 확정: ~/.local/bin + curl 직접 사용 (note #96/#97 덮어씀) |

---

## 8. 재발 방지 항목

| # | 패턴 | 제안 |
|---|------|------|
| 1 | 워커가 구현 완료 후 태스크 상태 미갱신 | demo 진입 전 반드시 `task_list` 조회 후 모든 태스크를 finished로 전이하는 체크리스트 강제화. engram-worker 에이전트 프롬프트에 "demo 전 task 전이 확인" 항목 추가 |
| 2 | context note와 실제 태스크 상태 불일치 | context note 작성 시 실제 `task_list` 호출 결과를 인용하도록 규칙 추가. "task_list(required): 없음"이라고 기재하기 전 반드시 조회 결과 확인 |
| 3 | 설계 변경 caveat가 2회 연속 미반영 (이슈 #24) | 이슈 재작업 시 모든 미해결 caveat를 워크스루하는 단계를 워커 시작 프롬프트에 포함. 특히 scope=issue인 caveat는 해당 이슈 재착수 시 필독 처리 |
| 4 | 설계 노트 상호 수정 (note #95 → #96 → #97 → #98) | 설계 결정이 확정되면 이전 노트를 resolved=true로 표시하여 최신 확정안(note #98)만 활성화. 노트 덮어쓰기 없이 명시적 resolved 처리 권장 |

---

## 9. 다음 스프린트 액션 아이템

| # | 항목 | 출처 | 담당 |
|---|------|------|------|
| 1 | 이슈 #24 — transition_to="working" 수정 반영 (engram-reviewer.md 8곳 + review-issue/SKILL.md 4곳) | note #106 CHANGES_REQUESTED | 워커 에이전트 |
| 2 | 이슈 #24 재demo 후 사용자 최종 승인 (finished 전이) | note #107 LGTM 잠정 승인 대기 | 사용자 |
| 3 | 이슈 #25 재demo 후 사용자 최종 승인 | note #107 LGTM 잠정 승인 대기 | 사용자 |
| 4 | 이슈 #35 재demo 후 사용자 최종 승인 | note #108 LGTM 잠정 승인 대기 | 사용자 |
| 5 | 이슈 #26 — README v0.5.0 업데이트 착수 (task #68, required 상태) | 선행 이슈 demo 완료 후 착수 가능 | 워커 에이전트 |
| 6 | engram-worker 프롬프트에 "demo 전 task 전이 체크리스트" 추가 | 패턴 A 재발 방지 | 리더/아키텍트 |
| 7 | Epic #6 스코프 caveat (note #95, #98) resolved 처리 — note #96, #97을 resolved=true로 표시 | 노트 정리 | 리더 |

---

## 부록 — 이슈 이력 요약

### 이슈 #24 상태 전이 이력

```
required → ready (claude-sonnet@review-check, 05:48)
ready → working (claude-sonnet@afb591c8-issue24, 05:58)
working → demo (claude-sonnet@afb591c8-issue24, 06:00)  ← 1차 demo 진입
demo → ready (engram-reviewer@a0873829, 06:06)          ← 1차 CHANGES_REQUESTED
ready → working (main@cleanup-issue24, 06:10)
working → demo (main@cleanup-issue24, 06:10)             ← 2차 demo 진입
demo → working (engram-reviewer@acb1dfae, 06:11)         ← 2차 CHANGES_REQUESTED
working → demo (main@cleanup-issue24, 06:15)             ← 3차 demo 진입 (현재)
```

총 3회 demo 진입, 2회 CHANGES_REQUESTED 처리.

### 이슈 #25 상태 전이 이력

```
required → ready (claude-sonnet@review-check, 05:48)
ready → working (claude-sonnet@afb591c8-issue25, 06:00)
working → demo (claude-sonnet@afb591c8-issue25, 06:02)  ← 1차 demo 진입
demo → ready (engram-reviewer@a0873829, 06:06)           ← 1차 CHANGES_REQUESTED
ready → working (main@cleanup-issue25, 06:10)
working → demo (main@cleanup-issue25, 06:10)             ← 2차 demo 진입 (현재)
```

총 2회 demo 진입, 1회 CHANGES_REQUESTED 처리.

### 이슈 #26 상태 전이 이력

```
required → ready (claude-sonnet@review-check, 05:48)
ready → working (claude-sonnet@afb591c8-issue26, 06:03)
working → demo (claude-sonnet@afb591c8-issue26, 06:08)  ← 1차 demo 진입 (현재)
```

총 1회 demo 진입. 리뷰 미진행.

### 이슈 #35 상태 전이 이력

```
required → ready (claude-sonnet@review-check, 05:48)
ready → working (claude-sonnet@afb591c8-issue35, 06:02)
working → demo (claude-sonnet@afb591c8-issue35, 06:03)  ← 1차 demo 진입
demo → ready (engram-reviewer@a0873829, 06:06)           ← 1차 CHANGES_REQUESTED
ready → working (main@cleanup-issue35, 06:10)
working → demo (main@cleanup-issue35, 06:10)             ← 2차 demo 진입 (현재)
```

총 2회 demo 진입, 1회 CHANGES_REQUESTED 처리.
