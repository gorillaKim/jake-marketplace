# Changelog

engram-orchestrator 플러그인의 버전별 변경 내역입니다.

---

## [0.10.0] — 2026-06-23

> 회고 기반 정확도·가드 개선 + engram 코어 신규 역량(evaluation note_type) 채택. (mission #73)

### Changed

- **조회 mode 규약 README SSOT화** — `mode="agent"`(목록·오리엔테이션) vs `mode="normal"`(본문 풀로드) 이원 규칙이 6개 에이전트/스킬 문서에 산재하던 것을 README `## 토큰 예산 / Payload 규칙` 하위 `### 조회 호출 mode 규약 (agent vs normal)` 단일 SSOT(테이블 + 식별자 파싱 예시)로 통합. analyzer/leader/worker/retro/reviewer + team-track 은 규약을 재서술하지 않고 동일 앵커를 링크 참조. 기존 `compact=true` 잔재 서술도 `mode="agent"` 기준으로 정정(마이그레이션 노트 1건만 보존). (#759, epic #210)
- **플러그인 평가노트 작성 → `note_type="evaluation"` 전환** — worker(Step 3.5)·solo-track·team-track 의 `[EVALUATION]` 피드백 노트를 `reference`+접두어 대신 engram 코어 신규 `note_type="evaluation"`(P1)로 작성. `[EVALUATION]` summary 접두어는 코어 백필 전 회고 fallback 호환을 위해 병행 유지. `[SKILL]`/`[RULE AUDIT]` 노트는 회고의 evaluation 집계 오염을 막기 위해 `reference` 유지. (#767 [J1], epic #212)
- **회고 평가 집계 → `note_type`·`epic_id` 조회 전환** — engram-retro 가 `[EVALUATION]` 텍스트 풀스캔 대신 `note_list(note_type="evaluation")` 로 평가 노트를 수집(에픽 단위는 `note_list(epic_id=N, note_type="evaluation", rollup=true)`, 코어 P1·P2). v0.10.0 이전 레거시 `reference`+`[EVALUATION]` 접두어 노트도 병행 수집(fallback). sprint-retro 리포트 §10 설명도 정합. (#768 [J2], epic #212)

### Added

- **engram-reviewer batch — 에픽 완료 제안(`epic_finish`)** — batch 검토 종료 시 하위 demo 이슈가 전수 LGTM 이고 `epic_get.ready_to_complete=true`(코어 P4)인 에픽을 식별해, 사용자에게 `AskUserQuestion` 으로 `epic_finish(epic_id, agent_id="user")` 를 **제안**. 에이전트는 `epic_finish` 를 직접 호출하지 않는다(`demo→finished` 와 동일하게 에픽 종결도 사용자 전용). batch 최종 보고에 "완료 후보 에픽" 라인 추가, review-issue 스킬 보고/주의사항도 정합. (#769 [J3], epic #212)
- **solo-track 벌크 코멘트 점검 가드** — 다수 이슈를 한 세션에서 직렬 처리할 때도 이슈마다 Step A.continue read #1(`note_list(note_type="comment")`)을 1회씩 수행하도록 가드 추가(흐름 내 명시 + 금지 항목). 벌크 승격 중 per-issue 사용자 코멘트 누락 회귀(#2024) 방지. (#760, epic #210)
- **동일 파일 다중 이슈 hunk 귀속 표준** — 커밋 없이 여러 이슈가 같은 파일을 수정할 때 context note "변경 파일" 에 이슈별 hunk(섹션/심볼/요지) 귀속을 명시하는 표준을 README Demo Gate(SSOT)에 정의. solo-track Step C 가드·Step D 템플릿, team-track `WORKER_RESULT.context_note` 가 이를 참조. 누적 `git diff` 에서 reviewer/사용자가 이슈별 변경분을 분리 검토 가능. (#761, epic #210)
- **analyzer 드래프트 파일·라인 귀속 검증** — 자동생성한 issue description/goal 이 파일·라인·심볼을 지목하면 `issue_create` 전에 `grep`/`rg` 로 실제 일치를 검증하고, 불일치 시 보정하거나 `[귀속 미검증]` 표기 + caveat 로 남기도록 Step 3·분할 가이드에 명시. 드래프트가 엉뚱한 파일을 지목해 워커가 헛수고하는 회귀(#2022·#662) 방지. (#762, epic #210)

### Migration

- version `0.9.0` → `0.10.0`.

---

## [0.9.0] — 2026-06-19

> 토큰 효율(`mode="agent"` 마이그레이션) + 에이전트/스킬 동작 정확도·사용성 개선. (mission #60)

### Changed

- **MCP 조회 호출 `compact=true` → `mode="agent"` 전면 마이그레이션** — 5개 에이전트(engram-analyzer/leader/worker/reviewer/retro)와 7개 스킬(team-track/solo-track/onboard/review-issue/sprint-retro/mission-plan/intake-as-issue)의 `session_restore`·`*_list` 오리엔테이션/목록 호출을 `mode="agent"`(LLM 친화 텍스트 요약)로 정렬. 본문 풀로드가 필요한 `issue_get`/`note_get` 은 `mode="normal"` 유지(2단계 페치 패턴). 플러그인 전체 `compact=true`/`--compact` 잔존 0건. CLI fallback 예시도 `engram session restore --mode agent --json` 으로 갱신. (epic #181)
- **`work-journaling` 스킬 → `team-track` 리네이밍** — 팀(analyzer→leader→worker) 이슈 처리 표준 절차 = `solo-track` 의 팀 카운터파트임을 이름으로 명확화(사용자 피드백 #2024). 디렉터리(`skills/team-track/`)·frontmatter·운영 참조 일괄 갱신. **호출 ID 변경(breaking)**: `/engram-orchestrator:work-journaling` → `/engram-orchestrator:team-track`. (아래 과거 버전 항목의 `work-journaling` 언급은 당시 실제 명칭이므로 보존.)

### Added

- **solo-track `Step D.6 — 세션 종료`** — 리뷰 패스(D.5) 종결 후 결과와 무관하게 `session_end` 를 호출하도록 명시(좀비 세션/`agent_id` 누적 방지). LGTM/CHANGES_REQUESTED 분기별 종료 시점 표 + 금지 항목 추가. (epic #183)
- **engram-leader: `WORKER_RESULT.skill_audit` → context note 연계** — worker 가 채우던 `skill_audit`(skills_unnecessary/rules_applied/skills_invoked)를 leader 가 context note 끝에 `[skill_audit]` 한 줄로 기록 → 회고(engram-retro)/skill-doctor 시그널로 환원.
- **intake-as-issue: 경계 케이스 예시 카드(6종)** — 2~3 task/한 PR 중간 경계에서 solo vs team 오판(false-positive)을 줄이는 구체 라우팅 표.
- **ui-qa-reviewer: 로그인 SKIP fallback 정책(Step 1.6)** — SKIP 시 spec 을 `code_reviewable`/`manual_check_required` 로 분류 반환(verdict=null). 로그인 SKIP 자체는 CHANGES_REQUESTED 사유 아님(오발동 방지). 결과 JSON 필드 추가, engram-reviewer 와 양방향 정합.

### Performance

- **engram-leader stalled 감시 주기 `session_restore` 중복 호출 제거** — 오리엔테이션은 세션 시작 1회만 호출·캐시, stalled 주기는 `stalled_issues`+`note_list` 만 호출(반복 주기당 토큰 절감).

### Migration

- version `0.8.0` → `0.9.0`.

---

## [0.8.0] — 2026-06-02

### UI 테스트/리뷰 (Playwright MCP 번들)

- **MCP 서버 번들 (`.mcp.json`)** — `playwright`(`npx -y @playwright/mcp@latest`, stdio) + `engram`(`http://127.0.0.1:3456/mcp`, http) 선언. 플러그인 활성화 시 자동 연결.
  - **engram 번들 근거(실측)**: 번들 서버는 표준형 `mcp__<servername>__` 으로 노출됨(`--plugin-dir` 로 playwright→`mcp__playwright__*` 확인). 따라서 `engram` 번들 → `mcp__engram__*` 로, 기존 `mcp__engram__*` 참조와 동일(깨지지 않음). 사용자가 같은 endpoint 로 이미 등록한 경우 **endpoint dedup + 상위 스코프 우선** 으로 흡수됨(다른 이름 `engramtest`→같은 URL 로딩 시 `mcp__engram__` 로 흡수되는 것 실측). 전제: Desktop 앱 가동(미가동 시 연결만 끊긴 상태, 로드엔 무해). *(초기 0.8.0 초안에서 "engram 번들 부적합" 으로 판단했으나, 네임스페이스 실측 결과로 철회 — 번들이 안전하며 신규 사용자에게 자동 제공 이점.)*
- **`ui-qa-reviewer` 서브에이전트 신설** — Playwright MCP 로 대상 URL 을 실제 브라우저에서 열어 스크린샷·접근성 스냅샷·인터랙션을 spec/AC 대비 PASS/FAIL 검증. plugin-shipped 제약상 `mcpServers` frontmatter 미사용(번들 MCP 를 세션 상속). **로그인 필요 페이지는 자동 로그인하지 않고 사용자에게 로그인 요청**(headed 브라우저 + AskUserQuestion, 자격증명 미요구/미저장), 취소 시 SKIPPED 처리.
- **`ui-test` 스킬 신설** — 트리거 "ui 테스트/UI 검증/화면 검증". 대상 URL+spec → ui-qa-reviewer spawn → 결과 보고(이슈 연동 시 note 기록).
- **engram-reviewer UI 분기 연동** — demo 이슈가 UI 성격(휴리스틱: 레이아웃/모달/반응형 등 키워드 + 명시 `[UI]`/`target_url` note)이고 검증 URL 확보 시 `ui-qa-reviewer` 를 spawn 해 브라우저 검증 결과를 LGTM/CHANGES_REQUESTED 판정에 종합. URL 미확보/로그인 불가 시 "UI 수동 확인 필요" caveat 후 코드 리뷰로 진행(오발동 방지). reviewer `tools` 에 `Agent` 추가.
- **solo-track / review-issue 정합** — solo 의 Step D.5(engram-reviewer spawn)가 UI 이슈를 자동 커버(reviewer 가 ui-qa-reviewer 중첩 spawn). onboard 에 Playwright 전제(node/npx) 점검 추가.
- version `0.7.0` → `0.8.0`.

## [0.7.0] — 2026-06-02

### 실행 모드 라우팅 (Solo vs Team) + Solo 리뷰 분리

- **`실행 모드 라우팅 (solo-track vs 팀)` 기준 신설** (README) — **solo 를 강한 기본값**으로, 팀은 *진짜 복잡한 예외*(동시 병렬 이득·worktree 격리·멀티 LLM 중 하나가 명확)에만. **이슈 개수는 약한 신호** — solo 는 여러 이슈도 직렬로 처리하므로 개수만으로 팀을 부르지 않는다. "judge → proceed": solo 는 바로 진행, 팀은 비용이 크므로 확인 후 진행.
- **`engram-analyzer` 가 분할 직후 `RECOMMENDED_MODE`(solo|team) + 근거를 반환** — 이슈 수·병렬 폭·충돌 위험을 실제 산출한 시점에 판정(가장 정확).
- **`intake-as-issue` 라우팅 재구성** — 기존 "문서 작업만 solo" 한정 힌트를 라우팅 기준 참조로 교체(코드 작업 포함). 사전(요청 텍스트)·사후(analyzer `RECOMMENDED_MODE`) 2단 판단 + `solo`→solo-track 자동 진행 / `team`→AskUserQuestion 확인 후 leader 트리거.
- **`solo-track` 매트릭스에 기준 SSOT 상호참조 추가**.
- **Solo 모드 리뷰 분리 (Step D.5 신설)** — solo 라도 *작성자 ≠ 리뷰어* 원칙 유지: demo 진입 후 메인이 직접 LGTM 하지 않고 **`engram-reviewer` 서브에이전트를 spawn** 해 독립 리뷰. CHANGES_REQUESTED 시 Step B 복귀. self-approve 를 금지 항목에 추가. ("solo" = 병렬 worker 미사용이지 모든 서브에이전트 미사용이 아님.)

### 토큰 효율 (Token Efficiency)

- **오리엔테이션 호출 `compact=true` 표준화** — 5개 에이전트(analyzer/leader/worker/reviewer/retro) 및 스킬(work-journaling/solo-track/onboard/review-issue/sprint-retro)의 `session_restore` 호출을 `compact=true`로 정렬. per-issue note/task 가 count 로 접히며 `active_caveats`/`active_missions` 는 보존되어 데이터 손실 없이 페이로드만 감소. (실측: 무필터 ~680KB → `project_key`+`compact` ~15KB, −98%)
- **이력 조회 `limit` 명시** — `engram-retro` / `solo-track` 의 `history_for` 호출에 `limit` 추가.
- **retro 1차 스캔 가이드** — `engram-retro` 이슈 수집 시 `issue_list(projection=[...])` 로 1차 스캔 후 필요한 이슈만 상세 수집하도록 안내.
- **신규 문서 섹션 `토큰 예산 / Payload 규칙`** (README) — "오리엔테이션은 가볍게(compact), 실제 소비할 본문만 풀로드" 원칙 + size guard 경고 대응 규칙 명문화. 각 에이전트/스킬이 이 섹션을 참조.

### 유지 (Unchanged by design)

- worker/reviewer/retro 가 **실제 소비**하는 작업·리뷰·회고 대상 이슈의 `issue_get(include_notes=true)` 풀로드는 그대로 유지 — compact 시 description/goal 이 잘리므로 본문이 필요한 경로엔 미적용 (안전 우선).

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
