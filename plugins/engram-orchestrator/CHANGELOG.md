# Changelog

engram-orchestrator 플러그인의 버전별 변경 내역입니다.

---

## [0.6.0] — 2026-05-25

### 추가 (Added)

- **미션(Mission) 레이어 통합 (ADR-0014)**
  - `engram-retro`: 회고 리포트에 "1. 미션 진행 현황 (Missions)" 섹션 추가 — 미션별 달성률 및 상태(완료/진행/지연) 분석.
  - `engram-analyzer`: `mission_list` / `mission_create` 호출 지원. 대규모 작업 시 미션 자동 수립 후 에픽 연결.
  - `engram-leader`: `session_restore` 응답의 `active_missions` 파싱, context note에 미션 목적 기록, stalled 판단에 미션 진행률 활용.
  - `engram-worker`: `issue_get` 응답의 `mission_id` 확인 → 미션 컨텍스트를 discovery/reference 노트에 반영.
  - `intake-as-issue`: 미션 연관성 확인 후 analyzer에 `hint_mission_id` 전달.
  - **신규 스킬 `mission-plan`**: 대형 프로젝트 로드맵 수립 전용. 트리거: "미션 계획", "로드맵", "분기 목표 설정".

- **스킬/하네스 피드백(EVALUATION) 시스템**
  - `engram-worker` / `solo-track`: 작업 완료 시 `[EVALUATION]` 피드백 노트 작성 의무화 (`note_type="reference"`, 접두사 `[EVALUATION]`).
  - `WORKER_RESULT.evidence`에 `evaluation_note_added: true` 필드 추가.
  - `work-journaling`: Step 3에 `[EVALUATION]` 표준 템플릿 정의 (하네스 평가 / 스킬 평가 / Engram 사용 피드백 / 개선 제안 4항목).

- **대화형 회고 인터랙션**
  - `engram-retro` Step F: 회고 리포트 작성 후 사용자에게 핵심 피드백 요약 보고 + 유도 질문 기반 상호작용 회고 세션 진행.
  - `sprint-retro` 스킬 흐름에 Step F 반영.

- **회고 리포트 10섹션 확장**
  - 기존 9섹션에 "10. 스킬 및 하네스 피드백 (Harness & Skill Feedback)" 섹션 추가.
  - 에이전트별 `[EVALUATION]` 피드백 목록 + 항목별 종합 요약(하네스/스킬/Engram/개선 제안).

### 변경 (Changed)

- `issue_create` 호출 시 `sprint_id` / `mission_id` 인자 제거 — 에픽으로부터 자동 상속 (ADR-0014).
- `engram-retro` 버전 표기: v0.5.0 → v0.6.0, frontmatter description 업데이트.

### 문서 (Documentation)

- `docs/migration.md`: v0.5.x → v0.6.0 마이그레이션 가이드 추가 (DB 자동 마이그레이션, API 변경, EVALUATION 의무화, 대화형 회고).

---

## [0.5.1] — 2026-05-20

### 수정 (Fixed)

- worker/leader/solo-track의 `git diff --name-only HEAD` → `git status --porcelain | awk '{print $2}'` 교체 — 신규(untracked) 파일이 git diff에 잡히지 않는 false-fail 해결.
- leader demo gate 실패 3-케이스 분류: A(파일 실재+task 불일치 → task 자동 정정 후 demo 재진입) / B(파일 없음 → ready 환원) / C(test 미통과 → ready 환원).

### 추가 (Added)

- worker/solo-track 금지 항목에 "작업 중 note_add 누락 금지"·"required task 잔존 시 demo 금지" 명시.
- intake-as-issue에 solo-track 라우팅 힌트 추가 — 문서 파일 5개 이하+코드 없음+신규 추가만 조건 시 solo-track 추천.

---

## [0.5.0] — 2026-05-18

### 추가 (Added)

- `engram-reviewer` 에이전트 + `review-issue` 스킬 (UC9).
- `engram-retro` 에이전트 + `sprint-retro` 스킬 (UC10).
- `onboard` 스킬 — CLI·Desktop·MCP 일괄 설치 온보딩.
- Agents 3→5, Skills 3→6 확장.

---

## [0.4.1] — 2026-05-15

### 추가 (Added)

- solo-track `Step A.continue` (이어 작업 분기): 5개 read 검토 + status/assigned_agent 매트릭스.
- leader 정체 감시 2단계 escalation: 단계 1 질문 코멘트 (`Q: stalled`) + 단계 2 미응답 +20분 후 AskUserQuestion.
- work-journaling `Step 2.5 Incoming Comment 체크`.

---

## [0.4.0] — 2026-05-12

### 추가 (Added)

- Hybrid 패턴 도입: worker = pure executor (상태 전이 도구 제거, WORKER_RESULT YAML 보고), leader = state machine driver.
- Evidence 자체 검증 (Anti-Hallucination 마지막 방어선).
- 신규 스킬 `solo-track` (UC8).

---

## [0.3.0] — 2026-05-08

### 추가 (Added)

- `issue_claim` / `issue_release` 패턴 채택, `agent_id` 명명 규칙 + 의무 주입.
- leader stalled `AskUserQuestion` 액션화 (release/handoff).

---

## [0.2.0] — 2026-05-04

### 변경 (Changed)

- tools 와일드카드 → 명시 나열, work-journaling Step 0~6, demo gate 자체 검증, anti-hallucination 인용 의무.

---

## [0.1.0] — 2026-05-01

### 추가 (Added)

- 초기 릴리스: engram-analyzer, engram-leader, engram-worker + intake-as-issue, work-journaling.
