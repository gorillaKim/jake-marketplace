# engram-orchestrator

Engram MCP 위에서 동작하는 **이슈 분석 / 리딩 / 처리 / 리뷰 / 회고** 에이전트 오케스트레이션 플러그인.

## 무엇을 하는가

```
[사용자 작업 요청]
        │
        ├──────────────────────┐
        ▼                      ▼
[intake-as-issue]       [mission-plan] ── 대형 프로젝트 로드맵 수립 및 일괄 수립
  (이슈화 확인)           (미션/에픽/이슈 일괄 계획)
        │                      │
        └──────────┬───────────┘
                   │
                   ▼
[engram-analyzer]   ── 작업을 여러 이슈로 분할
                      · 적합 에픽 매핑/생성
                      · task 다수 등록
                      · blocks 의존성 설정
                      · required → ready 까지만 전이
                      · agent_id 의무
        │
        ▼
[engram-leader]     ── ┌── ready 큐 조회 + active_workers 인식
   (state machine)     ├── 이슈마다 issue_claim 직접 (CAS 점유)
                       ├── engram-worker spawn (코드 작업만)
                       │     ▼
                       │   [engram-worker]
                       │       · Step 0: 코멘트/caveat 검토
                       │       · Step 1: 컨텍스트 + assigned_agent 확인
                       │       · Step 2: 코드 작업 + discovery/decision note
                       │       · Step 3: Demo gate 자체 수집 (task/test/git diff)
                       │       · Step 4: WORKER_RESULT 보고 (YAML)
                       │
                       ├── WORKER_RESULT 파싱 + evidence 자체 검증
                       │     (task_list / task_test_list / Bash git diff 재호출)
                       ├── 통과: task_update(finished) x N + note_add(context) + release(demo)
                       ├── 실패: caveat + release(ready)
                       └── stalled 정체: AskUserQuestion → release/handoff/그대로
        │
        ▼
[사용자 검토 대기]   ── demo 상태
        │
        ├── [engram-reviewer]  ── demo 이슈 코드 레벨 검토
        │       · Step A: 컨텍스트 수집 (단일 / batch)
        │       · Step B: 변경 파일 Read + git diff 확인
        │       · Step C: 판정 체크리스트 (6항목)
        │       · Step D: LGTM → context note + 사용자 안내
        │               CHANGES_REQUESTED → caveat note + release(ready)
        │
        └── [사용자]           ── demo → finished (에이전트 금지)

        ─────────────────────────────────────────────
        스프린트 종료 시

[engram-retro]      ── 스프린트 전체 이슈 분석 → 회고 문서 생성
                      · Step A: 스프린트 확정
                      · Step B: 이슈 전체 수집 (병렬)
                      · Step C: decision/discovery/blocker/caveat 분석
                      · Step D: 회고 마크다운 Write
                      · Step E: 요약 보고
```

## 제공

- **Agents** (5) — `tools` 필드는 명시 나열 (Claude Code 가 와일드카드 미지원).
  - `engram-analyzer` — 작업 분할 / 이슈·태스크·blocks 등록 (MCP create/update + Bash)
  - `engram-leader` — **state machine driver**. claim/release/task_update/context note + stalled 회수 전담 (MCP write 권한 + Agent + AskUserQuestion + Bash)
  - `engram-worker` — **pure executor**. 코드 작업 + discovery/decision note 만 (상태 전이 도구 없음). WORKER_RESULT YAML 로 leader 에게 보고.
  - `engram-reviewer` — **demo 이슈 코드 리뷰어**. 단일/batch 모드 지원. LGTM(승인) 또는 CHANGES_REQUESTED(변경요청) 판정. demo→finished 는 절대 호출하지 않음 (사용자 전용).
  - `engram-retro` — **스프린트 회고 생성기**. 이슈·노트 전체 분석 → 10섹션 마크다운 문서 생성. 읽기 전용 (상태 전이 없음).
- **Skills** (6)
  - `intake-as-issue` — 다단계 작업 요청만 이슈화 게이트
  - `mission-plan` — 대형 프로젝트 로드맵 수립 및 미션/에픽/이슈 일괄 계획
  - `work-journaling` — worker/leader 호출 권한 매트릭스 + Step 절차 + WORKER_RESULT 양식
  - `solo-track` — 메인 에이전트가 서브에이전트 없이 직접 작업할 때 issue/task/note 라이프사이클로 트래킹 (UC8)
  - `review-issue` — demo 이슈 코드 리뷰 트리거. engram-reviewer 를 spawn 하여 LGTM/CHANGES_REQUESTED 판정 (UC9)
  - `sprint-retro` — 스프린트 회고 문서 생성 트리거. engram-retro 를 spawn 하여 10섹션 마크다운 저장 (UC10)

## 빠른 시작

처음 설정하는 경우 온보딩 스킬로 CLI·Desktop·MCP 를 일괄 설치·등록한다:

```
/engram-orchestrator:onboard
```

또는 자연어: `"engram 온보딩 해줘"` / `"setup engram"`

온보딩 스킬이 다음을 자동 처리한다:
1. engram CLI 설치 (curl + GitHub Releases, ~/.local/bin)
2. Desktop 앱 설치 (DMG, 사용자 동의 후)
3. MCP 등록 (Claude Code / Claude Desktop)
4. 연결 검증 + 실패 시 CLI fallback 안내

## 전제 의존성

이 플러그인은 [Engram](../../../) MCP **v0.3 이상** 에 의존한다 (issue_claim/issue_release/agent_id/history_* 활용).

### 옵션 A — Engram 데스크톱 앱 (권장, HTTP)

```bash
claude mcp add --scope user --transport http engram http://127.0.0.1:3456/mcp
```

또는 `~/.claude.json` 의 `mcpServers` 에 직접 추가:

```json
{
  "mcpServers": {
    "engram": {
      "type": "http",
      "url": "http://127.0.0.1:3456/mcp"
    }
  }
}
```

> ⚠️ Claude Code CLI 인식 위치는 `~/.claude.json` 의 `mcpServers`.
> `~/.claude/settings.json` 의 `mcpServers` 는 무시되니 혼동 주의.

### 옵션 B — stdio 바이너리 직접 빌드

```bash
git clone <engram-repo>
cd engram
cargo install --path crates/engram-mcp --bin engram-mcp
```

### 플러그인 활성화

`~/.claude/settings.json`:
```json
{
  "enabledPlugins": {
    "engram-orchestrator@jake-plugins": true
  }
}
```

설정 변경 후 **Claude Code 재시작 필요**.

## Use Cases

이 플러그인이 지원하는 표준 시나리오들. v0.4.0 부터 모든 이슈 처리의 진입점은 `engram-leader` 이며, worker 직접 호출은 비권장 (state machine 분리 위반).

---

### UC1 — 사용자 요청을 이슈로 등록 (Intake → Analyzer)

**상황**: 사용자가 자연어로 비정형 작업 요청. 다단계 변경이 명백한 경우.

> "결제 영수증을 PDF 로 다운받을 수 있게 만들어줘"

**흐름**:

1. `intake-as-issue` 자동 트리거 → `AskUserQuestion("이슈로 만들어 처리할까요?")`.
2. 예 → `engram-analyzer` spawn (`agent_id="engram-analyzer@<sess>"`).
3. analyzer 가 적합 에픽 매핑/생성 → 이슈 2~3건 분할 → task 등록 → `issue_link(blocks)` 의존성 → `note_add(decision)` → 모든 신규 이슈 `issue_update(status="ready", agent_id=...)`.
4. 호출자에게 `epic_id, issue_ids[]` 보고.

```
사용자: "방금 만든 #128/#129/#130 처리해줘"
→ engram-leader 호출 (UC3 으로 이어짐)
```

---

### UC2 — 단일 이슈 직접 처리 (leader 가 claim-and-spawn)

**상황**: 이미 등록된 이슈 1개. v0.4.0 부터 leader 가 진입점.

```
사용자: "이슈 #142 작업해줘"

→ Agent(
    subagent_type='engram-orchestrator:engram-leader',
    prompt='Engram issue #142 처리. mode=claim-and-spawn.'
  )
```

**leader 의 동작**:

| Step | 호출 | 효과 |
|------|------|------|
| 1 | `issue_claim(142, agent_id="claude-opus@<sess>-issue142")` | CAS 점유 |
| 2 | `Agent(subagent_type='worker', prompt='... agent_id 주입 ...')` | 코드 작업 위임 |
| 3 | worker 의 WORKER_RESULT YAML 수신 | 결과 파싱 |
| 4 | `task_list(req)` / `task_test_list` / `Bash("git status --porcelain | awk '{print $2}'")` 재호출 | **evidence 자체 검증** |
| 5a | 통과 시: `task_update(finished) x N` + `note_add(context)` + `issue_release(demo)` | demo 진입 |
| 5b | 실패 시: `note_add(caveat)` + `issue_release(ready)` | 환원 |
| 6 | `session_end` | cleanup |

이후 사용자가 데스크톱 칸반에서 `demo → finished` 로 종결.

> 💡 leader 가 evidence 를 자체 호출로 재검증 → worker 가 "demo 진입했어요" 라고 거짓말해도 차단.

---

### UC3 — 여러 이슈 동시 병렬 (leader 가 N 워커 spawn)

**상황**: ready 큐에 이슈가 여러 개. claude 만으로 동시 처리.

```
사용자: "ready 큐 비워줘"

→ Agent(
    subagent_type='engram-orchestrator:engram-leader',
    prompt='project_key=jake-marketplace. mode=dispatch.'
  )
```

**leader 동작**:

1. `sprint_current` + `issue_list(status="ready")` + `my_blocked_issues` + `session_restore.active_workers` 조회.
2. blocked / 점유 중 제외하고 N 개 선택.
3. **이슈마다 spawn 사이클** (병렬 가능):

   ```
   # 각 이슈 N 에 대해
   worker_agent_id = f"claude-opus@<sess>-issue{N}"
   issue_claim(id=N, agent_id=worker_agent_id)  # leader 가 먼저 잡음
   Agent(subagent_type='worker', prompt='... agent_id 주입 ...')
   → WORKER_RESULT 받음 → evidence 검증 → release(demo|ready)
   ```

4. 동일 파일/모듈 가능성 이슈는 순차로.

**병렬 안전성 보장 (v0.4.0)**:
- **CAS claim 1차 방어** — issue 레벨 race 0%.
- **leader 의 evidence 자체 검증 2차 방어** — worker fake call 차단.

---

### UC4 — 멀티 LLM 라우팅 (claude + codex + gemini)

**상황**: 모델별 강점에 맞춰 분배.

leader 가 issue description 키워드로 모델 분기 + spawn 명령 분기:

```
# leader 가 issue #N 의 description 검토 후
if has_keyword(["test", "테스트"]) in description:
    worker_agent_id = f"codex-gpt5@<sess>-issue{N}"
    issue_claim(N, worker_agent_id)
    worker_result = Bash(f"omc team 1:codex '... agent_id={worker_agent_id}. WORKER_RESULT 보고.'")

elif has_keyword(["prototype", "프로토타입"]):
    worker_agent_id = f"gemini-2.5@<sess>-issue{N}"
    issue_claim(N, worker_agent_id)
    worker_result = Bash(f"omc team 1:gemini ...")

else:
    worker_agent_id = f"claude-opus@<sess>-issue{N}"
    issue_claim(N, worker_agent_id)
    worker_result = Agent(subagent_type='engram-worker', prompt='...')

# 어느 모델이든 동일한 WORKER_RESULT 양식
handle_worker_result(N, worker_agent_id, worker_result)
```

**왜 v0.4.0 이 멀티 LLM 친화적인가**:
- codex/gemini 가 work-journaling Step 0~4 만 따르면 됨 — claim/release 안 따져도 leader 가 처리.
- WORKER_RESULT evidence 가 모델별 거짓말을 강제로 잡음 (leader 의 Bash 검증).
- `agent_id` 별 history 로 모델별 활동량 추적 가능.

---

### UC5 — 광역 규칙 공지 (project / sprint / epic scope caveat)

**상황**: "결제 모듈 손대지 마", "마이그레이션 직전이라 schema 변경 금지" 같은 광역 규칙.

```
note_add(
  scope="project",
  project_key="jake-marketplace",
  note_type="caveat",
  author="user",
  agent_id="user",
  summary="결제 모듈 코드 변경은 사전 승인 필요",
  detail="..."
)
```

**전파**: 어느 워커가 어느 이슈를 잡든 Step 1 의 `session_restore(project_key)` 응답에 `active_caveats[]` 로 자동 노출. 워커는 검토 후 위반 시 `note_add(caveat)` 보고 → WORKER_RESULT.status="blocked".

**해제**: `note_resolve(<note_id>, agent_id="user")` — 사용자만.

---

### UC6 — 정체 이슈 회수 (stalled → release / handoff / force)

**상황**: 한 워커가 죽거나 느려져 working 상태 N 분 이상 정체.

```
사용자: "지금 막힌 이슈 있어?"

→ Agent(subagent_type='engram-orchestrator:engram-leader',
        prompt='project_key=jake-marketplace. mode=monitor.')
```

**leader 동작 — 2단계 escalation (v0.4.1)**:

#### 단계 1 — 1차 검출 (stalled 후 10분): 질문 코멘트

1. `stalled_issues({project_key, threshold_minutes: 10})` 호출.
2. 정체 이슈마다 중복 `Q: stalled` comment 확인 → 있으면 단계 2.
3. `history_by_agent(agent_id=<해당 워커>, limit=5)` — 다른 이슈에서 활동 흔적 발견 시 caveat 만 (`stalled Nm — agent active elsewhere`) + escalation 보류.
4. 진짜 정체 시 **질문 코멘트** (`caveat` 가 아닌 `comment`):

   ```
   note_add(issue_id=N, note_type="comment", author="agent",
            agent_id="engram-leader@<sess>",
            summary=f"Q: stalled {minutes}m — 아직 작업 중인가요?",
            detail="점유 워커: <...> / 응답 protocol / 30분 후 escalation")
   ```

5. 사용자에게 짧게 보고 — "워커 응답 대기 30분".

#### 단계 2 — 응답 시한 만료 (stalled 후 총 30분): AskUserQuestion

다음 leader 사이클 마다 미해결 stalled-question 코멘트 확인:

1. `note_list(comment, include_resolved=false)` + `note_get` 으로 `created_at` 확인.
2. `created_at + 20분` (총 30분) 까지 `resolved=false` 면 escalation 발동:

   ```
   AskUserQuestion: "#125 30분+ 정체. 어떻게 처리할까요?"
     - release (ready 환원)
     - handoff (새 워커로 재시도, UC4 모델 분기 가능)
     - 그대로 두기
   ```

3. **release**: `issue_release(125, agent_id=<해당 워커>, transition_to="ready")`. 권한 거부 시 `force=true, agent_id=engram-leader@<sess>` 강제 회수.
4. **handoff**: 위 release → UC4 spawn 사이클을 다른 모델로 재실행.

#### 응답 가능 actor 매트릭스

| Actor | 답변 방법 |
|-------|----------|
| 점유 워커 (claude/codex/gemini) | work-journaling **Step 2.5 incoming check** 가 트리거. `note_add(comment, agent_id=<self>)` + `note_resolve`. 단 같은 이슈로 다음 leader 사이클에 재 spawn 됐을 때만 가능 (Claude Code 동기 모델 한계). |
| 사용자 (데스크톱) | `note_add(comment, author="user")` + `note_resolve` 또는 직접 release. **가장 흔한 응답자.** |
| leader 본인 | 단계 1.3 의 `history_by_agent` 점검에서 워커가 다른 이슈에 활동 중 확인 → 질문 코멘트 추가하지 않고 caveat 만 + escalation 보류. |

**지속 감시**: `/loop 10m /engram-orchestrator:engram-leader project_key=xxx mode=monitor`.

---

### UC7 — 사후 활동 추적 / 데일리 다이제스트

**상황**: 어제 / 지난 1시간 동안 누가 무엇을 했는지 한눈에.

```
# 1) 크로스 엔티티 최근 변경
history_recent({since_minutes: 1440, limit: 100})

# 2) 특정 에이전트만 필터
history_by_agent({agent_id: "claude-opus@a4b2c8-issue142", limit: 50})

# 3) 한 이슈의 라이프사이클 (시간순)
history_for({entity_type: "issue", entity_id: 128})
```

**활용 패턴**:

| 시점 | 호출 | 가치 |
|------|------|------|
| 매일 아침 점검 | `history_recent(since_minutes=1440)` | 어제 demo 진입 / ready 환원 / caveat 발생 요약 |
| 모델별 활동량 비교 | `history_by_agent` 패턴별 | 어느 모델이 가장 많은 작업 처리했는지 |
| 이슈 사후 감사 | `history_for(issue, N)` | claim → working → release(demo) 전 흐름 + 누가 했는지 |
| 사고 조사 | `history_for(issue, N)` 후 의심 transition 의 `changed_by` 확인 | 누가 언제 잘못된 전이 시도했는지 |

**v0.4.0 의 history 패턴**:
- `worker_agent_id` (예: `claude-opus@<sess>-issue142`) → discovery/decision note 작성자.
- `engram-leader@<sess>` → 모든 상태 전이 (claim/release/task_update/context note) 의 actor.
- `engram-analyzer@<sess>` → 이슈 분할 + ready 전이.
- `user` → 데스크톱에서 finished 처리, broadcast caveat 작성.

각 actor 의 행동이 명확히 분리되어 멀티 LLM + 멀티 사용자 환경에서도 추적 가능.

---

### UC8 — Solo Track (메인 에이전트 직접 처리, 서브에이전트 spawn 없음)

**상황**: 1~3 task 한 PR 분량의 가벼운 작업. analyzer/leader/worker 3-agent 분리가 오버킬이지만 **기록은 남기고 싶음**.

```
사용자: "이 함수 리네이밍하면서 트래킹해줘"
       또는 "engram 으로 기록하면서 처리"
       또는 "/engram-orchestrator:solo-track ..."

→ Skill('engram-orchestrator:solo-track')
```

**메인 에이전트가 단일 actor 로 Step A → Step E 수행** (서브에이전트 spawn 없음):

| Step | 호출 | 효과 |
|------|------|------|
| A | **분기**: 사용자가 `issue_id` 명시 → **A.continue** (5개 read 후 status/assigned_agent 매트릭스 분기, 안전 claim). 미명시 → **A.new** (`issue_create` + `task_create x N` + `issue_update(ready)` + `issue_claim`). | 분할(압축) + 점유 |
| B | 코드 작업 + `note_add(discovery/decision)` + `task_update(finished, agent_id)` | 작업 + 실시간 기록 |
| C | `task_list(req)` + `task_test_list` + `Bash("git status --porcelain | awk '{print $2}'")` | Demo Gate 자체 검증 |
| D | `note_add(context)` + `issue_release(transition_to="demo")` | demo 진입 |
| E | `session_end` | cleanup |

**Step A.continue (이어 작업, v0.4.1 신규)** — 사용자가 `issue_id` 명시 시 반드시 다음 5개 read 호출:

```
1. note_list(comment), 2. note_list(caveat), 3. session_restore,
4. issue_get(include_tasks=true, include_notes=true), 5. history_for(issue, N)
```

상태별 분기 (자세히는 `skills/solo-track/SKILL.md`):
- `ready` + assigned_agent=null → claim 가능
- `working` + 본인 → `issue_release(ready)` 후 재 claim
- `working` + 다른 agent → 점유 중, claim 금지 + 사용자 보고
- 그 외 → 작업 불가, 사용자 보고

`agent_id` 형식: `main@<sess>-issue<N>`. 모든 호출에 동일 식별자.

**언제 solo-track 인가**:

| 시나리오 | 선택 |
|---------|------|
| 단일 task 텍스트 편집 | ❌ 직접 처리 (이슈 등록 없음) |
| **1~3 task 한 PR + 기록 원함** | ✅ **solo-track** |
| 다중 PR / 여러 모듈 | UC2~4 (engram-leader) |
| 큰 요구사항 분할 후 진행 | UC1 (intake → analyzer) |

---

### UC9 — 코드 리뷰 (engram-reviewer, review-issue 스킬)

**상황**: demo 상태 이슈의 코드를 검토하여 승인 또는 변경요청.

```
사용자: "demo 이슈 리뷰해줘"
       또는 "#128 코드 리뷰"
       또는 "/engram-orchestrator:review-issue"

→ Skill('engram-orchestrator:review-issue')
→ Agent(subagent_type='engram-orchestrator:engram-reviewer', ...)
```

**reviewer 의 동작**:

| Step | 호출 | 효과 |
|------|------|------|
| A | `session_restore` + `issue_get` (단일) 또는 `epic_list` + `issue_list(demo)` (batch) | 컨텍스트 수집 |
| B | context note 읽기 → `Read(<변경파일>)` + `Bash("git diff --name-only HEAD~1 HEAD")` | 실제 파일 검토 |
| C | 6항목 판정 체크리스트 (task/test/context note/코드실재/패턴/사이드이펙트) | 판정 |
| D-LGTM | `note_add(context, "LGTM")` + 사용자 finished 안내 | 승인 |
| D-CR | `note_add(caveat, "CHANGES_REQUESTED")` + `issue_release(ready)` | 변경요청 + 환원 |

> ⚠️ `demo → finished` 는 **사용자 전용**. reviewer 는 절대 호출하지 않음.

**트리거**: `"리뷰해줘"`, `"코드 리뷰"`, `"review"`, `"demo 검토"`, `"LGTM 확인"`, `"승인"`, `"변경요청"`

---

### UC10 — 스프린트 회고 (engram-retro, sprint-retro 스킬)

**상황**: 스프린트 종료 후 (또는 중간 시점에) 회고 문서 자동 생성.

```
사용자: "회고해줘"
       또는 "이번 스프린트 회고 문서 만들어줘"
       또는 "/engram-orchestrator:sprint-retro"

→ Skill('engram-orchestrator:sprint-retro')
→ Agent(subagent_type='engram-orchestrator:engram-retro', ...)
```

**retro 의 동작**:

| Step | 호출 | 효과 |
|------|------|------|
| A | `sprint_current` + `sprint_list` → finished 우선, 없으면 active | 스프린트 확정 |
| B | `issue_list` + 각 이슈 `issue_get` + `history_for` + `note_list` 4종 (병렬) | 전체 이슈 수집 |
| C | decision/discovery/blocker_detail/caveat 추출 + 빈도 분석 + 액션 아이템 도출 | 노트 분석 |
| D | `AskUserQuestion(저장 경로)` → `Write(9섹션 마크다운)` | 문서 생성 |
| E | 완료/미완료/액션 아이템 요약 보고 | 보고 |

**회고 문서 10섹션**: 미션 진행 현황 / 스프린트 요약 / 완료된 것 / 미완료 / 주요 결정 / 발견·배운 것 / 블로커 분석 / 반복 주의사항 / 재발 방지 / 다음 스프린트 액션 아이템 / 스킬 및 하네스 피드백

**트리거**: `"회고해줘"`, `"retro"`, `"스프린트 리뷰"`, `"retrospective"`, `"회고 문서"`, `"이번 스프린트 정리"`

---

## 실행 모드 라우팅 (solo-track vs 팀)

이슈로 등록할 작업을 **누가 처리할지** 결정하는 기준. 분할 규모가 드러나는 시점(**analyzer 분할 직후가 가장 정확** — 이슈 수/병렬 폭/충돌 위험을 이미 안다)에 적용한다.

결정 신호는 **이슈 개수가 아니라 "동시 처리·격리·멀티 LLM 이득이 worker N개 spawn 비용을 넘느냐"** 다. solo-track 은 이슈가 여러 개라도 한 세션에서 **직렬로 거뜬히 처리**한다 — 개수만으로 팀을 부르지 않는다.

| 신호 | solo-track (메인 직접, 직렬) | 팀 (leader + worker, 동시) |
|------|----------------------------|---------------------------|
| 이슈 수 | 다수라도 OK (개수는 **약한 신호**) | 개수보다 아래 신호가 결정 |
| 병렬 폭 (서로 blocks 없는 독립 이슈) | 직렬로 충분 | **동시 처리 이득이 분명**할 만큼 충분히 많고 각 이슈가 무거움 |
| 파일/모듈 충돌 위험 | 없음 또는 순차로 회피 가능 | 있음 → **worktree 격리** 이득 |
| 멀티 LLM 라우팅 (codex/gemini 병행) | ❌ | ✅ |
| 이슈 1건당 작업량 | 작거나 보통 (순차가 빠름) | 크고 독립적 → 분산이 전체 처리 시간 단축 |

**판정** (solo 강하게 선호):
- **기본값은 solo-track. 가능한 한 solo 에 의존한다.** 이슈가 여럿이어도 직렬로 처리해도 무방하면 solo-track 으로 순차 진행한다.
- **팀은 "진짜 복잡한" 예외에만** — 다음 중 하나가 **명확할 때만** 팀으로 승급:
  1. 독립적이고 무거운 이슈가 **동시에 여럿**이라 병렬 spawn 이 전체 처리 시간을 실질적으로 줄인다.
  2. 파일/모듈 충돌로 **worktree 격리**가 필요하다.
  3. **멀티 LLM 라우팅**(codex/gemini 병행)이 필요하다.
- 위 셋 중 어느 것도 강하게 해당하지 않으면 → **solo-track**. 경계·모호도 solo 우선 (오버헤드가 작아 false-positive 비용이 낮다).

> **리뷰는 solo 모드에서도 서브에이전트로 분리한다.** solo-track 은 *병렬 worker* 를 띄우지 않을 뿐, **review 패스는 반드시 `engram-reviewer` 서브에이전트를 spawn** 한다 — 작성자(메인)와 리뷰어를 다른 컨텍스트로 분리해 자기 승인(self-approve)을 막기 위함. 즉 "solo = 직접 작업 + 독립 리뷰어", "팀 = leader 분배 + worker + 리뷰어".

**진행 (judge → proceed)**:
- **solo 판정** → 저비용이므로 **바로 solo-track 으로 진행**.
- **팀 판정** → 워커 N개 spawn 은 비용이 크므로 **추천 + `AskUserQuestion` 확인 후** leader 트리거. (사용자가 즉시 진행을 명시했으면 확인 생략)

---

## 토큰 예산 / Payload 규칙

Engram MCP(v0.1.36+)는 응답 페이로드를 줄이는 인자를 제공한다. 멀티 에이전트가 반복 호출하는 환경에서 누적 토큰을 크게 좌우하므로, 모든 에이전트·스킬은 아래 규칙을 따른다.

| 상황 | 규칙 |
|------|------|
| **오리엔테이션 호출** (`session_restore`, `board_status`) | 항상 `compact=true`. per-issue note/task 가 count 로 접히며 `active_caveats`/`active_missions` 는 그대로 보존 → 손실 없이 페이로드만 감소 |
| **프로젝트가 정해진 경우** | `session_restore(project_key, compact=true)` — `project_key` 필터가 단일 프로젝트 컨텍스트만 끌어와 가장 큰 절감 |
| **목록 조회** (`issue_list`, `epic_list`) | `project_key`/`status`/`sprint_id` 필터 우선. 대량이면 `limit`(+`offset`) 페이지네이션 + `projection=[...]` 로 필요한 필드만 |
| **이력 조회** (`history_for`/`history_recent`/`history_by_agent`) | `limit` 명시 (기본 50/20, 최대 500) |
| **실제로 소비할 본문** (작업/리뷰/회고 대상 이슈의 `issue_get`, retro 의 `note_list`) | `include_notes=true` 풀로드 **유지** — compact 시 description/goal 이 잘리므로 본문이 필요한 곳엔 쓰지 않는다 |
| **size guard 경고 수신** | 응답의 `truncated:true` / `warnings` 가 오면 `project_key` 로 범위를 좁혀 재호출 |

> 실측(Sprint260521): `session_restore` 무필터 ~680KB → `project_key` 필터 ~17.5KB(−97%) → `+compact` ~15KB(−98%).

핵심 원칙: **오리엔테이션은 가볍게(compact), 실제 소비할 본문만 풀로드.**

---

## 핵심 안전 장치 (v0.4.0)

### Hybrid 패턴 (state machine 분리)

- **worker** = pure executor. 코드 작업 + note(discovery/decision/blocker_detail/caveat) 만.
- **leader** = state machine driver. claim/release/task_update/context note 전담.
- worker 에게 상태 전이 도구를 **물리적으로 안 줌** → "한 척" 사고 불가능.

### Evidence 자체 검증 (Anti-Hallucination 마지막 방어선)

worker 의 WORKER_RESULT.evidence (git diff, task list, test check) 를 leader 가 **동일 호출로 재실행**. 결과 불일치 시 release(demo) 거부 + caveat + ready 환원.

```
worker.evidence.git_diff_files = ["src/x.ts"]   # 보고
leader.Bash("git status --porcelain | awk '{print $2}'") = []   # 실제
→ Demo gate fail. release(ready). caveat 기록.
```

### Claim/Release 패턴 (race 방지)

- leader Step 1: `issue_claim(id, worker_agent_id)` — CAS 점유. 두 워커가 같은 이슈 못 잡음.
- leader Step 5: `issue_release(id, worker_agent_id, transition_to="demo|ready")` — ownership 해제 + 전이.
- stalled 회수: `issue_release(force=true, agent_id=engram-leader@<sess>)` 사용자 승인 후.

### agent_id 의무

| Actor | 식별자 형식 |
|-------|------------|
| analyzer | `engram-analyzer@<sess>` |
| leader | `engram-leader@<sess>` |
| worker | `<model>@<sess>-issue<id>` (예: `claude-opus@a4b2c8-issue142`) |
| reviewer | `engram-reviewer@<sess>` |
| retro | `engram-retro@<sess>` |
| user | `user` |

`history_by_agent` / `history_for` / `history_recent` 가 의미를 가지려면 모든 호출에 agent_id 필수.

### Demo Gate (3단 검증)

worker Step 3 자체 수집 → WORKER_RESULT.evidence → leader 자체 재호출 검증. 한 단계라도 실패하면 demo 전이 차단.

## 상태 전이 가드

모든 에이전트는 다음을 **절대 호출하지 않는다**:

- `issue_update(status="finished")` — 사용자 검토 완료 신호
- `issue_update(status="cancelled")` — 사용자 작업 포기 신호

위반은 `history_by_agent` 로 추적되어 사후 감사 가능.

## 알려진 한계 (멀티 에이전트 병렬 시나리오)

engram MCP v0.3 기준 한계 (v0.4.0 플러그인이 우회/완화한 항목 표시):

- **task 레벨 claim 없음** — v0.4.0 leader 가 이슈 단위 직렬화로 우회 ✓
- **sub-agent fake call** — v0.4.0 Hybrid 패턴 + evidence 자체 검증으로 차단 ✓
- **lease 자동 만료 없음** — 죽은 워커가 잡은 이슈는 stalled_issues 발견 + 사용자 승인 후 leader 가 force release. 자동 회수는 미구현.
- **push 알림 없음** — stalled/status_change 이벤트가 외부로 push 되지 않아 leader 가 polling. `/loop` 결합 필요.
- **project_create MCP 없음** — 새 프로젝트는 데스크톱 UI 에서 먼저 생성해야 함.

위 잔여 한계는 engram 측에 SSE / issue_renew 가 들어오면 해소되며, 플러그인 측 후속 업데이트로 따라간다.

## 함께 자주 쓰는 도구

- Engram MCP `stalled_issues` — leader 의 정체 감지 단일 호출
- Engram MCP `history_recent / history_by_agent / history_for` — 멀티 에이전트 사후 추적
- Engram MCP `note_type="comment"` — 사용자 ↔ 에이전트 대화 (CommentSection UI 와 정합)

## 버전

- **0.6.0** — 미션 레이어 정합화 (ADR-0014), 스킬/하네스 피드백(EVALUATION) 시스템 도입 및 대화형 회고 보강. (1) engram-retro 미션 단위 회고 및 에이전트 [EVALUATION] 피드백을 수집·종합하는 "10. 스킬 및 하네스 피드백" 섹션을 추가하고 회고 완료 후 대화형 인터랙션(Step F) 가이드 도입. (2) engram-analyzer 이슈 분할 시 미션 연동 및 `issue_create`에서 `sprint_id`/`mission_id` 제거 (에픽 자동 상속). (3) engram-leader `active_missions` 파싱, context note에 미션 목적 기록 및 stalled 판단 보강. (4) engram-worker 및 solo-track 작업 중/완료 시 하네스, 스킬 사용 적절성, Engram 토큰 평가를 남기는 [EVALUATION] 노트 작성을 의무화하고 WORKER_RESULT의 evidence에 반영. (5) intake-as-issue 미션 연관성 확인 및 analyzer에 hint_mission_id 전달 흐름 반영. (6) mission-plan 대형 프로젝트 로드맵 수립 신규 스킬 추가 (트리거: "미션 계획", "로드맵", "분기 목표 설정"). (7) 플러그인 버전 bump 및 마이그레이션 가이드 추가.
- **0.5.1** — 버그픽스 + 안정화. (1) worker/leader/solo-track의 `git diff --name-only HEAD` → `git status --porcelain | awk '{print $2}'` 교체 — 신규(untracked) 파일이 git diff에 잡히지 않는 false-fail 해결. (2) leader demo gate 실패 3-케이스 분류: A(파일 실재+task 불일치 → task 자동 정정 후 demo 재진입) / B(파일 없음 → ready 환원) / C(test 미통과 → ready 환원). (3) worker/solo-track 금지 항목에 "작업 중 note_add 누락 금지"·"required task 잔존 시 demo 금지" 명시. (4) intake-as-issue에 solo-track 라우팅 힌트 추가 — 문서 파일 5개 이하+코드 없음+신규 추가만 조건 시 solo-track 추천.
- **0.5.0** — engram-reviewer 에이전트 + review-issue 스킬 추가 (UC9). engram-retro 에이전트 + sprint-retro 스킬 추가 (UC10). onboard 스킬 추가 — CLI·Desktop·MCP 일괄 설치 온보딩 (curl + ~/.local/bin, note #93~#98 반영). Agents 3→5, Skills 3→5(+onboard). 플로우 다이어그램에 reviewer/retro 경로 추가. agent_id 테이블에 reviewer/retro 추가.
- **0.4.1** — solo-track `Step A.continue` (이어 작업 분기) 추가: 5개 read 검토 + status/assigned_agent 매트릭스. leader 정체 감시 2단계 escalation 도입: 단계 1 질문 코멘트 (`Q: stalled`) + 단계 2 미응답 +20분 후 AskUserQuestion. work-journaling `Step 2.5 Incoming Comment 체크` 추가 — 워커가 매 task 진입 직전 1회 leader 의 질문 코멘트에 응답.
- **0.4.0** — Hybrid 패턴 도입. worker = pure executor (상태 전이 도구 제거, WORKER_RESULT YAML 보고). leader = state machine driver (claim → spawn → evidence 자체 검증 → task_update + context note + release). Anti-hallucination 의 마지막 방어선 추가. UC2/3/4 진입점을 leader 로 통일. 신규 스킬 `solo-track` 추가 — 메인 에이전트가 서브에이전트 spawn 없이 직접 1~3 task 분량을 issue/task/note 라이프사이클로 트래킹 (UC8).
- 0.3.0 — issue_claim/issue_release 패턴 채택 (Step 2/5), agent_id 명명 규칙 + 의무 주입, leader 의 stalled AskUserQuestion 액션화 (release/handoff), worker Step 6 자기 claim 안전 회수, history_* 도구 활용.
- 0.2.0 — tools 와일드카드 → 명시 나열, work-journaling Step 0~6, demo gate 자체 검증, anti-hallucination 인용 의무, project_key 결정 절차, intake 트리거 게이트 강화, README HTTP 우선.
- 0.1.0 — 초기 릴리스.

## MCP 미지원 환경 — CLI fallback

서브에이전트가 Agent SDK 의 tool whitelist 로 MCP 도구를 못 받거나, 호스트가 stdio MCP 서버에 못 붙는 환경에서는 `engram` CLI 가 동일한 동작을 1:1 로 제공한다. ADR-0010 + `docs/cli-mcp-parity.md` (engram repo) 가 45 MCP 도구 ↔ CLI verb 의 동치를 보장하고, `crates/engram-cli/tests/parity_test.rs` 15 통합 테스트가 회귀를 자동 차단.

설치: `engram` repo 의 [`docs/plugin-setup.md`](https://github.com/<owner>/engram/blob/main/docs/plugin-setup.md) 참조 (cargo install 또는 GitHub Releases prebuilt).

### 1. 세션 시작 — `session_restore` 대체

```bash
engram session restore --project myproj --json
```

### 2. 이슈 점유 — `issue_claim` 대체 (CAS 안전)

```bash
engram issue claim 12 --agent-id "claude-opus@$SESS-issue12" --json
# 이미 다른 워커가 점유 중이면 exit 2 (Validation) — agent_id 충돌
```

### 3. demo 전이 — `issue_release(transition_to=demo)` 대체

```bash
engram issue release 12 \
  --agent-id "claude-opus@$SESS-issue12" \
  --transition-to demo --json
```

### 4. 컨텍스트 노트 — `note_add(scope=issue, type=context)` 대체

```bash
engram note add --issue 12 --type context \
  --summary "demo 진입 — 검토 가이드" \
  --detail "산출물: ...\n검토 포인트: ..." \
  --agent-id "claude-opus@$SESS-issue12" --json
```

### 5. broadcast decision — `note_add(scope=epic)` 대체

```bash
engram note add --type decision \
  --summary "분할 근거 — ..." \
  --detail "..." \
  --scope epic --scope-target-id 4 \
  --agent-id "engram-analyzer@$SESS" --json
```

### 6. 정체 감지 — `stalled_issues` 대체 (leader)

```bash
engram stalled --threshold-minutes 10 --project myproj --json
```

### 7. 변경 이력 — `history_*` 대체 (감사)

```bash
engram history recent --since-minutes 30 --json
engram history by-agent --agent-id "claude-opus@$SESS-issue12" --limit 20 --json
engram history for --entity-type issue --entity-id 12 --json
```

### exit code 매핑 (ADR-0010 §4)

| exit | 의미                                        | 권장 동작                       |
|------|--------------------------------------------|--------------------------------|
| 0    | 성공                                       | 다음 단계 진행                  |
| 1    | DB/Migration/기타 anyhow                  | stop & report                  |
| 2    | Validation (CAS 거부 포함)                 | 인자 수정 또는 다른 이슈 전환    |
| 3    | NotFound                                  | 대상 ID 재조회 후 결정           |
| 4    | InvalidTransition                          | backoff 또는 다른 경로          |

`--json` 모드에서는 stderr 에 `{"error":{"code":"...","message":"..."}}` 페이로드가 함께 emit.

### agent_id 규칙 (CLI 도 동일)

- 본인 식별자 명시: `claude-opus@<sessionShortId>-issue<issueId>` 등. `--agent-id user` 사칭 금지.
- `note_add` / `issue_claim` / `issue_release` / `issue_update` / `task_update` 모두 `--agent-id` 권장. 미지정 시 CLI 는 `"user"` 로 fallback.
- 전체 매핑/예시는 engram repo 의 [`docs/cli-mcp-parity.md`](https://github.com/<owner>/engram/blob/main/docs/cli-mcp-parity.md) 참조.
